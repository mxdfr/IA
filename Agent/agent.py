import os
import time
from xml.etree.ElementInclude import default_loader
import pandas as pd
import flask
import werkzeug.serving
from owlready2 import *
from owlready2.sparql.endpoint import *

# Ignore useless warnings
warnings.filterwarnings("ignore")

class Agent:
    PROT_SCORE = 1
    ontology_atoms_memory = set([])
    tweets_atoms_memory = set([])
    ontology_properties_memory = set([])
    tweets_properties_memory = set([])
    awaiting_stories = {}

    def __init__(self, ontology, tweets, folder_name):

        self.ontology_source = ontology
        self.tweets_source = tweets

        self.ontology = self.open_ontology(ontology)

        self.update_ontology_atoms_memory()
        self.update_tweets_atoms_memory()
        self.update_ontology_properties_memory()
        self.update_tweets_properties_memory()

        self.test_functions()

        self.start(folder_name)

    def test_functions(self):
        print("CONSEQUENTS")
        print(self.get_consequents(self.ontology.Running, "not isBadFor", -1))
        print("CHECK PROPERTY")
        print(self.check_property(self.ontology.Running, "usesBodyPart", self.ontology.Knee))


    def open_ontology(self, ontology):
        # Load the desired ontology using the path file
        Ontology = get_ontology(ontology).load()

        # Run the reasoner to obtain the inferences
        with Ontology:
            sync_reasoner(infer_property_values=True)

        return Ontology

    def start(self, folder_name):
        # Start the agent
        # Look for stories in queue:
        self.update_awaiting_stories(folder_name)

        # If there are stories, process them
        if len(self.awaiting_stories) > 0:
            # returns a list of tuples [(class, score)]
            self.process_stories()
            # Call the util function
        else:
            time.sleep(25)
            self.start()


    
    def update_awaiting_stories(self, folder_name):
        """
        Veronika
        Check for new txt files in stories folder and update self.awaiting_stories = dictionary {key=story, value=tuple(domain, property, range)}
        """

        if os.path.isdir(folder_name):
            if not os.listdir(folder_name):
                print("Directory is empty")
            else:    
                print("Directory is not empty")
        else:
            print("Given directory doesn't exist")
            exit()
        pass

    def process_stories(self):
        # Process all the stories in the queue
        for story in self.awaiting_stories:
            self.process_story(story)
            self.awaiting_stories.remove(story)

    def classify_statements(statements, property):
        return [], []

    def process_story(self, story):
        """
        If you cant find P->Q directly then extract all P's relations (with all its properties), classify them
        We only care to classify P's properties

        The loop should be: while the sources can bounce off eachother
        e.g. P causes obesity (causes = enhances ++)
        """
        # Process the story
        (object1, property, object2) = self.extract_query(story)
        # Check if the atoms are in the ontology:
        if property not in self.ontology_properties_memory.union(self.tweets_properties_memory):
            print("Sorry, I don't know this property!")
            return
        if object1 not in self.ontology_atoms_memory.union(self.tweets_atoms_memory):
            print(f"Sorry, I don't know this object: {object1}!")
            return
        if object2 not in self.ontology_atoms_memory.union(self.tweets_atoms_memory):
            print(f"Sorry, I don't know this object: {object2}!")
            return

        # If both atoms are in the ontology, check if the property is in the ontology
        knowledge_base = {1: self.ontology_atoms_memory, -1: self.tweets_atoms_memory}

        story_confirmed_by = []
        story_denied_by = []
        story_true = False
        for kb in knowledge_base:
            if object1 in knowledge_base[kb] and object2 in knowledge_base[kb]:
                # If the property is in the ontology, check which statements possitively/negatively influence the range
                scores, statements = self.check_property(object1, property, object2, ontology_type=kb)
                if statements:
                    story_confirmed_by, story_denied_by = self.classify_statements(statements, property)

            elif object1 in knowledge_base[kb] and object2 in knowledge_base[-1 * kb]:
                # If the objects are in two different ontologies, try to make a joint inference
                print("I don't know, but I'll ask my friends!")
                # look for all consequents with every property that is linked to object 1
                scores, consequents = self.get_consequents(object1, property, ontology_type=kb)

                if consequents:
                    story_confirmed_by, story_denied_by = self.classify_statements(consequents, property)

                # loop over them and check if they are in the other knowledge base:
                for c in consequents:
                    # if yes, check if there is a connection between the consequent and the object 2
                    if c in knowledge_base[-1 * kb]:
                        scores, statements = self.check_property(c, property, object2, ontology_type=kb)
                        if statements:
                            story_true = True
                            story_confirmed, story_denied = self.classify_statements(consequents, property)
                            story_confirmed_by += story_confirmed
                            story_denied_by += story_denied


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

        prop_to_check = self.ontology_properties_memory if ontology_type == 1 else self.tweets_properties_memory

        scores, relations = self.get_consequents(object1, property, ontology_type)
        for rel in enumerate(relations):
            if object2 in rel[1]:
                return [scores[rel[0]]], [relations[rel[0]]]

        return [0], []


    # def get_classes_instances(self, superClass):
    #     """
    #     Return all the subclasses with their instances
    #     """
    #     classes_and_instances = [superClass] + superClass.instances()
    #     print(classes_and_instances)
    #     for Class in superClass.subclasses():
    #         subclasses = self.get_classes_instances(Class)
    #         # classes_and_instances += classes_and_instances + subclasses

    #     return classes_and_instances


    def get_consequents(self, object1, property, ontology_type=1):
        """
        Object1 should be an owl object and property a string/label
        Check for all possible consequents of applying the property on the object1
        """

        consequents = []
        statement_scores = []
        if ontology_type == 1:
            consequents = list(default_world.sparql("""
                                PREFIX table:<http://www.semanticweb.org/weron/ontologies/2022/8/24okt#>
                                SELECT ?cons
                                { ?? table:""" + property + """ ?cons }
                            """, [object1]))

            statement_scores = [self.PROT_SCORE] * len(consequents)
        else:
            # extract consequents from mock_tweets_db
            tweets_opened = pd.read_excel(self.tweets_source)

            domains = []
            for antec in tweets_opened["predecessor atom"]:
                domains.append(antec.split(", "))

            ranges = []
            for cons in tweets_opened["successor atom"]:
                ranges.append(cons.split(", "))

            for range in enumerate(list(tweets_opened['relation'])):
                if range[1] == property and str(object1.label[0]).lower() in domains[range[0]]:
                    # calc trustworthyness
                    statement_scores.append(0)
                    consequents += ranges[range[0]]

        return statement_scores, consequents

    def update_ontology_atoms_memory(self):
        # Update the ontology atoms memory
        """
        Hiba
        Get all the classes and the instances from the ontology
        Returns a list
        """

        # Add ontology classes to the memory
        self.ontology_atoms_memory = self.ontology_atoms_memory.union(self.ontology.classes())
        # For each class, add its instances to the memory
        for concept in self.ontology_atoms_memory:
            self.ontology_atoms_memory = self.ontology_atoms_memory.union(self.ontology.get_instances_of(concept))

        print(self.ontology_atoms_memory)

        pass

    def update_ontology_properties_memory(self):
        # Update the ontology properties memory
        """
        Hiba
        Get all the object properties from the ontology
        Returns a dictionary with the properties as the key and their type of class as the value
        """
        # Add ontology properties to the memory
        self.ontology_properties_memory = self.ontology_properties_memory.union(self.ontology.properties())
        print(self.ontology_properties_memory)

        pass

    def update_tweets_atoms_memory(self):
        # Update the tweets atoms memory

        # open the csv file with tweets:
        tweets_opened = pd.read_excel(self.tweets_source)
        # get the atoms from the tweets:
        tweets_atoms = list(tweets_opened['predecessor atom'].unique()) + list(tweets_opened['successor atom'].unique())
        #tweets_atoms.append(tweets_opened['successor atom'].unique())
        # add them to the memory:
        self.tweets_atoms_memory = self.tweets_atoms_memory.union(tweets_atoms)
        print(self.tweets_atoms_memory)

    def update_tweets_properties_memory(self):
        # Update the tweets properties memory

        # open the csv file with tweets:
        tweets_opened = pd.read_excel(self.tweets_source)
        # get the properties from the tweets:
        tweets_properties = list(tweets_opened['relation'].unique())
        # add them to the memory:
        self.tweets_properties_memory = self.tweets_properties_memory.union(tweets_properties)
        print(self.tweets_properties_memory)

if __name__ == "__main__":
    # Run the agent
    agent = Agent(ontology="../OntologyVersions/24oktober.owl", tweets="./tweet_db.xlsx", folder_name="./Stories")

    pass
