from genericpath import exists
import os
from trust_scores import all, agent
from trust_network import create_trust_network
import time
from xml.etree.ElementInclude import default_loader
import pandas as pd
import flask
import werkzeug.serving
from owlready2 import *
from owlready2.sparql.endpoint import *

# for trust computation:
from trust_network import create_trust_network
from trust_scores import all as base_scores
from trust_scores import agent as agent_scores

# Ignore useless warnings
warnings.filterwarnings("ignore")

class Agent:
    PROT_SCORE = 1
    ontology_atoms_memory = set([])
    tweets_atoms_memory = set([])
    ontology_properties_memory = set([])
    tweets_properties_memory = set([])
    dict_ontology_properties = {}
    awaiting_stories = {}

    def __init__(self, ontology, tweets, folder_name):

        self.ontology_source = ontology
        self.tweets_source = tweets
        self.trust_scores = create_trust_network(base_scores, agent_scores)

        self.ontology = self.open_ontology(ontology)

        self.update_ontology_atoms_memory()
        self.update_tweets_atoms_memory()
        self.update_ontology_properties_memory()
        self.update_tweets_properties_memory()

        self.stories_folder_name = folder_name
        self.start()


    def open_ontology(self, ontology):
        # Load the desired ontology using the path file
        Ontology = get_ontology(ontology).load()

        # Run the reasoner to obtain the inferences
        with Ontology:
            sync_reasoner(infer_property_values=True)

        return Ontology

    def start(self):
        # Start the agent
        # Look for stories in queue:
        self.update_awaiting_stories()


        # If there are stories, process them
        print(self.awaiting_stories)
        if len(self.awaiting_stories) > 0:
            # returns a list of tuples [(class, linked inferences, score)]
            self.process_stories()
        else:
            time.sleep(25)
            self.start()

        time.sleep(25)
        self.start()
    
    def update_awaiting_stories(self):
    #Check for new txt files in stories folder and
    # update self.awaiting_stories = dictionary {key=story, value=tuple(domain, property, range, story name)}

        if os.path.isdir(self.stories_folder_name):
            if not os.listdir(self.stories_folder_name):
                print("Directory is empty")
            else:
                stories = os.listdir(self.stories_folder_name)
                for story in stories:
                    with open(self.stories_folder_name + "/"+ story, "r") as f:
                        story_content = f.read()
                        for line in story_content.splitlines():
                            if line.startswith("Domain:"):
                                domain = line.split(":")[1]
                            elif line.startswith("Property:"):
                                property = line.split(":")[1]
                            elif line.startswith("Range:"):
                                range = line.split(":")[1]
                        self.awaiting_stories[story] = (domain, property, range, story)
                    # os.remove(self.stories_folder_name +'/'+story)
        else:
            print("Given directory doesn't exist")
            exit()
        pass

    def process_stories(self):
        # Process all the stories in the queue
        for story in self.awaiting_stories:
            print("PROCESSING: ", story)
            results = self.process_story(story)
            if results:
                self.utility_function(results)
            else:
                print("Sorry could not find any information on that!!!")

        self.awaiting_stories = {}

    def classify_statements(self, statement):
        found_negative = False
        for property in range(1, len(statement), 2):
            if self.dict_ontology_properties[statement[property]] == 'decreases':
                if found_negative:
                    found_negative = False
                else:
                    found_negative = True

        if found_negative:
            return 'decreases'
        else:
            return 'increases'


    def make_linked_inferences(self, arguments, onto_consequents, tweet_consequents, domain, property, scores):
        index = 0
        for linked_inferences in enumerate(arguments):
            if domain == linked_inferences[1][1][-1]:
                index = 0
                for cons in onto_consequents + tweet_consequents:
                    Class = self.classify_statements(linked_inferences[1][1] + [property, cons[0]])

                    arguments.append((scores[index] + linked_inferences[1][0], linked_inferences[1][1] + [property, cons[0]], Class))

                index += 1

        return arguments


    def exists(self, object, memory):
        for obj in memory:
            if isinstance(obj, str):
                if obj == object:
                    return True
            elif obj.label[0] == object:
                return True

        return False

    
    def process_story(self, story):
        """
        If you cant find P->Q directly then extract all P's relations (with all its properties) and classify them
        We only care to classify P's properties

        The loop should be: while the sources can bounce off eachother
        """
        # Process the story
        (object1, property, object2) = self.extract_query(story)[:3]
        # Check if the atoms are in the ontology:
        if property not in self.dict_ontology_properties.keys() and property not in self.tweets_properties_memory:
            print("Sorry, I don't know this property!")
            return None
        if not self.exists(object1, self.ontology_atoms_memory.union(self.tweets_atoms_memory)):
            print(f"Sorry, I don't know this object: {object1}!")
            return None
        if not self.exists(object2, self.ontology_atoms_memory.union(self.tweets_atoms_memory)):
            print(f"Sorry, I don't know this object: {object2}!")
            return None

        for obj in self.ontology_atoms_memory.union(self.tweets_atoms_memory):
            if not isinstance(obj, str):
                if obj.label[0] == object1:
                    object1 = obj
                if obj.label[0] == object2:
                    object2 = obj

        # If both atoms are in the ontology, check if the property is in the ontology
        knowledge_base = {1: self.ontology_atoms_memory, -1: self.tweets_atoms_memory}

        arguments = [(0, [object1], "")]
        if not isinstance(object1, str):
            for s in self.get_subclasses(object1):
                arguments.append((0, [s], ""))
        domains = [object1]
        subs = self.get_subclasses(object2)
        for kb in knowledge_base:
            while domains:
                onto_scores, onto_properties = self.get_relations(domains[0], ontology_type=kb)
                tweet_scores, tweet_properties = self.get_relations(domains[0], ontology_type=-1 * kb)
                properties = onto_properties + tweet_properties
                scores = onto_scores + tweet_scores
                if properties:
                    for p in properties:

                        if isinstance(p, str):
                            label = p
                        else:
                            label = p.label[0]
                        onto_scores, onto_consequents = self.get_consequents(domains[0], label, ontology_type=kb)
                        tweet_scores, tweet_consequents = self.get_consequents(domains[0], label, ontology_type=-1 * kb)
                        consequents = onto_consequents + tweet_consequents
                        scores = onto_scores + tweet_scores
                        arguments = self.make_linked_inferences(arguments, onto_consequents, tweet_consequents, domains[0], label, scores)
                        for obj in zip(scores, consequents):
                            if not (object2 == obj[1][0] or object2.label[0] == obj[1][0])  or obj[1][0] in subs:# and property == label:
                                domains += obj[1]

                new_arguments = []
                for arg in enumerate(arguments):
                    if domains[0] != arg[1][1][-1] or arg[1][1][-1] in subs:
                        new_arguments.append(arg[1])

                arguments = new_arguments

                if not isinstance(domains[0], str):
                    domains += self.get_subclasses(domains[0])
                domains.pop(0)

        return arguments


    def get_subclasses(self, object):
        # Get subclasses of a given object
        subclasses = []
        objects_to_check = [object]
        flag = True
        while flag:
            flag = False
            are_instances = []
            while objects_to_check:
                subs = list(default_world.sparql("""
                                PREFIX table:<http://www.semanticweb.org/weron/ontologies/2022/8/24okt#>
                                SELECT ?class
                                { ?class rdfs:subClassOf* ?? }
                                """, [objects_to_check[0]]))

                subs = self.flatten(subs)
                subs = [sub for sub in subs if sub != objects_to_check[0]]

                if len(subs) != 0:
                    flag = True
                    subclasses += subs
                    objects_to_check += subs
                elif objects_to_check[0] not in are_instances and objects_to_check[0] in list(self.ontology.classes()):
                    inst = objects_to_check[0].instances()
                    are_instances += inst
                    flag = True
                    subclasses += inst
                    objects_to_check += inst

                x = objects_to_check.pop(0)

            subclasses = self.flatten(subclasses)
            subclasses = list(dict.fromkeys(subclasses))

        return subclasses


    def extract_query(self, story):
        """
        Extract the query from the story
        """
        # assumption: property is a tuple (A, B) where A is the exact property and B is the class of properties in ontologies

        return self.awaiting_stories[story]

    def check_property(self, object1, property, object2, ontology_type=1):
        """
        Check if the property is true between the two objects, in the given ontology
        ontology_type=1 is ontology, ontology_type=-1 is tweets
        
        For now it returns the score of the statement
        If they are not related then it returns 0
        """

        scores, relations = self.get_consequents(object1, property, ontology_type)
        for rel in enumerate(relations):
            if object2 in rel[1]:
                return [scores[rel[0]]], [relations[rel[0]]]

        return [0], []


    def flatten(self, l):
        ll = []
        for elem in l:
            if type(elem) == list:
                ll += self.flatten(elem)
            else:
                ll.append(elem)

        return ll


    def get_relations(self, object1, ontology_type=1):
        """
        Object1 should be an owl object and property a string/label
        Check for all possible consequents of applying the property on the object1
        """

        consequents = []
        statement_scores = []
        if ontology_type == 1:
            consequents = list(default_world.sparql("""
                                PREFIX table:<http://www.semanticweb.org/weron/ontologies/2022/8/24okt#>
                                SELECT DISTINCT ?property
                                { ?? rdf:type [owl:onProperty ?property] }
                                """, [object1]))

            consequents = [item for sublist in consequents for item in sublist]

            statement_scores = [self.PROT_SCORE] * len(consequents)
        else:
            # extract consequents from mock_tweets_db
            tweets_opened = pd.read_excel(self.tweets_source)

            domains = []
            for antec in tweets_opened["predecessor atom"]:
                domains.append(antec.split(", "))

            for prop in enumerate(list(tweets_opened['relation'])):
                if isinstance(object1, str):
                    label = object1
                else:
                    label = object1.label[0]

                if str(label) in domains[prop[0]]:
                    # calc trustworthyness
                    statement_scores.append(0)
                    consequents.append(prop[1]) # +prop
                
                consequents = list(dict.fromkeys(consequents))

        return statement_scores, consequents


    def get_consequents(self, object1, property, ontology_type=1):
        """
        Object1 should be an owl object and property a string/label
        Check for all possible consequents of applying the property on the object1
        """

        consequents = []
        statement_scores = []
        if ontology_type == 1:
            consequents += list(default_world.sparql("""
                                PREFIX table:<http://www.semanticweb.org/weron/ontologies/2022/8/24okt#>
                                SELECT ?cons
                                { ?? table:""" + property + """ ?cons }
                            """, [object1]))

            statement_scores = [self.PROT_SCORE] * len(consequents)
        else:
            # extract consequents from mock_tweets_db
            tweets_opened = pd.read_excel(self.tweets_source)

            UserID = []
            for id in tweets_opened["UserID"]:
                UserID.append(id)

            domains = []
            for antec in tweets_opened["predecessor atom"]:
                domains.append(antec.split(", "))

            ranges = []
            for cons in tweets_opened["successor atom"]:
                ranges.append(cons.split(", "))

            for range in enumerate(list(tweets_opened['relation'])):
                if isinstance(object1, str):
                    label = object1
                else:
                    label = object1.label[0]
                if range[1] == property and str(label) in domains[range[0]]:
                    # calc trustworthyness
                    statement_scores.append(create_trust_network(all, agent)[UserID[range[0]]]['e'])
                    consequents += [ranges[range[0]]]

        return statement_scores, consequents

    def update_ontology_atoms_memory(self):
        # Update the ontology atoms memory
        """
        Get all the classes and the instances from the ontology
        Returns a list
        """

        # Add ontology classes to the memory
        self.ontology_atoms_memory = self.ontology_atoms_memory.union(self.ontology.classes())
        # For each class, add its instances to the memory
        for concept in self.ontology_atoms_memory:
            self.ontology_atoms_memory = self.ontology_atoms_memory.union(self.ontology.get_instances_of(concept))

        pass

    def properties_dictionary(self):
        self.dict_ontology_properties = {}
        for property in self.ontology_properties_memory:
            if property.comment:
                self.dict_ontology_properties[property.label[0]] = property.comment[0]

    def update_ontology_properties_memory(self):
        # Update the ontology properties memory
        """
        Get all the object properties from the ontology
        Returns a dictionary with the properties as the key and their type of class as the value
        """
        # Add ontology properties to the memory
        self.ontology_properties_memory = self.ontology_properties_memory.union(self.ontology.properties())

        self.properties_dictionary()

        pass

    def update_tweets_atoms_memory(self):
        # Update the tweets atoms memory

        # open the csv file with tweets:
        tweets_opened = pd.read_excel(self.tweets_source)
        # get the atoms from the tweets:
        tweets_atoms = list(tweets_opened['predecessor atom'].unique()) + list(tweets_opened['successor atom'].unique())
        # add them to the memory:
        self.tweets_atoms_memory = self.tweets_atoms_memory.union(tweets_atoms)

    def update_tweets_properties_memory(self):
        # Update the tweets properties memory

        # open the csv file with tweets:
        tweets_opened = pd.read_excel(self.tweets_source)
        # get the properties from the tweets:
        tweets_properties = list(tweets_opened['relation'].unique())
        # add them to the memory:
        self.tweets_properties_memory = self.tweets_properties_memory.union(tweets_properties)

    def utility_function(self, statements):
        """
        Function for calculating utility
        :param true_statement_scores: list of trustworthiness scores for statements that make the story true
        :param false_statement_scores: list of trustworthiness scores for statements that make the story false
        :return: difference between the two total trustworthiness scores
        """
        true_statement_scores = [statement[0] for statement in statements if statement[2] == 'increases']
        true_statement = [statement[1] for statement in statements if statement[2] == 'increases']
        false_statement_scores = [statement[0] for statement in statements if statement[2] == 'decreases']
        false_statement = [statement[1] for statement in statements if statement[2] == 'decreases']
        print("\n\nThese are the inferences found in the ontology and the external source with their trustworthiness scores\n")
        print("Inference rules that justify with the story:\n")
        for true in zip(true_statement, true_statement_scores):
            for rule in true[0][:-1]:
                print(str(rule), end = " -> ")
            print(true[0][-1], " ", true[1])

        print("\n\nInference rules that falsify with the story:\n")
        for false in zip(false_statement, false_statement_scores):
            for rule in false[0][:-1]:
                print(str(rule), end = " -> ")
            print(false[0][-1], " ", false[1])

        if sum(true_statement_scores) - sum(false_statement_scores) >= 0:
            print("\n\nFrom the linked inference we can see that the story is true\n")
        else:
            print("\n\nFrom the linked inference we can see that the story is false\n")


if __name__ == "__main__":
    # Run the agent
    agent = Agent(ontology="../OntologyVersions/24oktober.owl", tweets="./tweet_db.xlsx", folder_name="stories_storage")

    pass
