from owlready2 import *
from pprint import pprint

# Ignore useless warnings
warnings.filterwarnings("ignore")

class Agent:

    def __init__(self, path="onto_pizza.owl"):
        # Load the desired ontology using the path file
        self.ontology = get_ontology(path)
        self.ontology.load()

        # Run the reasoner to obtain the inferences
        with self.ontology:
            sync_reasoner(infer_property_values=True)

        # Additional
        # Reference dictionaries between IRIs and given labels that might be useful
        self.label_to_class = {ent.label[0]: ent for ent in self.ontology.classes()}
        self.label_to_prop = {prop.label[0]: prop for prop in self.ontology.properties()}

        self.class_to_label = {ent: ent.label[0] for ent in self.ontology.classes()}
        self.prop_to_label = {prop: prop.label[0] for prop in self.ontology.properties()}

        # Save types to help differentiate between classes and properties later on
        self.class_type = type(list(self.ontology.classes())[0])
        self.propery_type = type(list(self.ontology.properties())[0])