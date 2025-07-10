import spacy
nlp = spacy.load("es_core_news_md")
doc = nlp("Este equipo tiene una fuente de poder 1250W con certificación 80 Plus Platinum.")
for ent in doc.ents:
    print(ent.text, ent.label_)
