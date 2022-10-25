import time
import pandas as pd

class Agent:
    ontology_atoms_memory = set([])
    tweets_atoms_memory = set([])
    ontology_properties_memory = set([])
    tweets_properties_memory = set([])
    awaiting_stories = []

    def __init__(self, ontology, tweets):

        self.ontology_source = ontology
        self.tweets_source = tweets

        self.update_ontology_atoms_memory()
        self.update_tweets_atoms_memory()
        self.update_ontology_properties_memory()
        self.update_tweets_properties_memory()

        self.start()

        pass

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

    def check_property(self, object1, property, object2, ontology_type=1, neg=False)\
            -> (float, bool):
        """
        Check if the property is true between the two objects, in the given ontology
        ontology_type=1 is ontology, ontology_type=-1 is tweets
        """

        if ontology_type == 1:
            # ontology
            pass
        elif ontology_type == -1:
            # tweets

            pass


        return 0, False

    def get_consequents(self, object1, property, ontology_type=1, neg=False) \
            -> (float, bool):
        """
        Check for all possible consequents of applying the property on the object1
        """
        return 0, False

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
    agent = Agent(ontology="./ontology.csv", tweets="./tweet_db.xlsx")

    pass
