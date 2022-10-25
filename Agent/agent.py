from owlready2 import *
from pprint import pprint

# Ignore useless warnings
warnings.filterwarnings("ignore")

class Agent:

    def __init__(self, path="file:///Users/rivka/Desktop/24oktober.owl"):
        # Load the desired ontology using the path file
        self.ontology = get_ontology(path)
        self.ontology.load()

        # Run the reasoner to obtain the inferences
        with self.ontology:
            sync_reasoner(infer_property_values=True)
        
        # Additional
        # Reference dictionaries between IRIs and given labels that might be useful
        
        print(self.ontology.type)
        self.label_to_class = {ent.label[0]: ent for ent in self.ontology.classes()}
        self.label_to_prop = {prop.label[0]: prop for prop in self.ontology.properties()}

        self.class_to_label = {ent:ent.label[0] for ent in self.ontology.classes()}
        self.prop_to_label = {prop:prop.label[0] for prop in self.ontology.properties()}
        

        # Save types to help differentiate between classes and properties later on
        self.class_type = type(list(self.ontology.classes())[0])
        self.propery_type = type(list(self.ontology.properties())[0])
        
    def sanity_check(self):
        # Display the labels (the names given in Protege) of all the classes & properties present in the ontology 
        pprint(self.class_reference_dict)
        prpint(self.prop_reference_dict)
    
    def simple_queries(self):
        print("Query responses:")

        # Get all the classes with the label ending in "_topping"
        # results = self.ontology.search(label="*_topping")
        # class_results = [self.class_to_label[result] for result in results if type(result) == self.class_type]
        # pprint(class_results)
        
        print("-" * 75)

        # Get all the classes that have "Vegetarian" as a superclass
        results2 = self.ontology.search(subclass_of=self.ontology.search_one(label="Symptoms"))
        subclasses = [self.class_to_label[result] for result in results2 if type(result) == self.class_type]
        pprint(subclasses)
