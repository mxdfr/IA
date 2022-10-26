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
    awaiting_stories = []

    def __init__(self, ontology, tweets):

        self.ontology_source = ontology
        self.tweets_source = tweets

        self.ontology = self.open_ontology(ontology)

        self.update_ontology_atoms_memory()
        self.update_tweets_atoms_memory()
        self.update_ontology_properties_memory()
        self.update_tweets_properties_memory()

        self.test_functions()

        self.start()

        pass

    def test_functions(self):
        print("CONSEQUENTS")
        print(self.get_consequents(self.ontology.Running, "usesBodyPart"))
        print("CHECK PROPERTY")
        print(self.check_property(self.ontology.Running, "usesBodyPart", self.ontology.Knee))


    def open_ontology(self, ontology):
        # Load the desired ontology using the path file
        Ontology = get_ontology(ontology).load()

        # Run the reasoner to obtain the inferences
        with Ontology:
            sync_reasoner(infer_property_values=True)

        # app = flask.Flask("Owlready_sparql_endpoint")
        # endpoint = EndPoint(default_world)
        # app.route("/sparql", methods = ["GET"])(endpoint)

        # werkzeug.serving.run_simple("localhost", 5000, app)

        return Ontology

    def start(self):
        # Start the agent
        # Look for stories in queue:
        self.update_awaiting_stories()

        # If there are stories, process them
        if len(self.awaiting_stories) > 0:
            self.process_stories()
        else:
            time.sleep(25)
            self.start()

    def process_stories(self):
        # Process all the stories in the queue
        for story in self.awaiting_stories:
            self.process_story(story)
            self.awaiting_stories.remove(story)

    def process_story(self, story):
        # Process the story
        (object1, property, object2) = self.extract_query(story)
        # Check if the atoms are in the ontology:
        if property[0] not in self.ontology_properties_memory.union(self.tweets_properties_memory):
            print("Sorry, I don't know this property!")
            return
        if object1 not in self.ontology_atoms_memory.union(self.tweets_atoms_memory):
            print(f"Sorry, I don't know this object: {object1}!")
            return
        if object2 not in self.ontology_atoms_memory.union(self.tweets_atoms_memory):
            print(f"Sorry, I don't know this object: {object2}!")
            return

        property = property[1]
        # If both atoms are in the ontology, check if the property is in the ontology
        knowledge_base = {1: self.ontology_atoms_memory, -1: self.tweets_atoms_memory}

        story_confirmed_by = []
        story_denied_by = []
        for kb in knowledge_base:
            if object1 in knowledge_base[kb] and object2 in knowledge_base[kb]:
                # If the property is in the ontology, check if the property is true
                evidence, found = self.check_property(object1, property, object2, ontology_type=kb)
                evidence_neg, found_neg = self.check_property(object1, property, object2, ontology_type=kb, neg=True)
                if found:
                    story_confirmed_by.append(evidence)
                elif found_neg:
                    story_denied_by.append(evidence_neg)

            elif object1 in knowledge_base[kb] and object2 in knowledge_base[-1 * kb]:
                # If the objects are in two different ontologies, try to make a joint inference
                print("I don't know, but I'll ask my friends!")
                # look for all consequents of applying the property on the object 1
                partial_evidence, consequents = self.get_consequents(object1, property, ontology_type=kb)

                # loop over them and check if they are in the other knowledge base:
                for c in consequents:
                    # if yes, check if there is a connection between the consequent and the object 2
                    if c in knowledge_base[-1 * kb]:
                        evidence, found = self.check_property(object1, property, object2, ontology_type=kb)
                        if found:
                            story_confirmed_by.append(partial_evidence + evidence)

                partial_neg_evidence, neg_consequents = self.get_consequents(object1, property, ontology_type=kb, neg=True)

                # loop over them and check if they are in the other knowledge base:
                for c in neg_consequents:
                    # if yes, check if there is a connection between the consequent and the object 2
                    if c in knowledge_base[-1 * kb]:
                        neg_evidence, neg_found = self.check_property(object1, property, object2, ontology_type=kb, neg=True)
                        if neg_found:
                            story_confirmed_by.append(partial_neg_evidence + neg_evidence)

    def extract_query(self, story):
        """
        Extract the query from the story
        """
        # assumption: property is a tuple (A, B) where A is the exact property and B is the class of properties in ontologies

        return "", "", ""

    def check_property(self, object1, property, object2, ontology_type=1, neg=False):
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
                return scores[rel[0]], True

        return 0, False


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


    def get_consequents(self, object1, property, ontology_type=1, neg=False):
        """
        Object1 should be an owl object and property a string/label
        Check for all possible consequents of applying the property on the object1
        """

        consequents = []
        statement_scores = []
        if ontology_type == 1:
            consequents = list(default_world.sparql("""
                                PREFIX table:<http://www.semanticweb.org/weron/ontologies/2022/8/food_and_stuff#>
                                SELECT ?cons
                                { ?? table:""" + property + """ ?cons }
                            """, [object1]))

            statement_scores = [self.PROT_SCORE] * len(consequents)
        else:
            # extract consequents from mock_tweets_db
            pass

        return statement_scores, consequents

    def update_ontology_atoms_memory(self):
        # Update the ontology atoms memory

        pass

    def update_ontology_properties_memory(self):
        # Update the ontology properties memory

        pass

    def update_awaiting_stories(self):
        # Update the stories in the queue

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
    agent = Agent(ontology="../ontology24okt.owl", tweets="./tweet_db.xlsx")

    pass
