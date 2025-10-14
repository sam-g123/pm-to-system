import spacy

class TaskParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        # TODO: Add custom NER pipe: self.nlp.add_pipe("ner", last=True)
    
    def parse_task(self, text):
        doc = self.nlp(text)
        entities = {
            "tasks": [ent.text for ent in doc.ents if ent.label_ == "TASK"],  # Custom labels later
            "deadlines": [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        }
        return entities