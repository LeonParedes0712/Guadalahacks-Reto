from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

frases = [

    # EMERGENCY
    "ayuda urgente",
    "necesito ayuda",
    "auxilio",
    "socorro",
    "estoy en peligro",
    "tengo miedo",
    "llama a alguien",
    "save me",

    # MUSIC
    "pon musica",
    "reproduce musica",
    "pon una cancion",
    "musica relajante",
    "musica triste",
    "pon rock",
    "pon reggaeton",

    # PRODUCTIVITY
    "tengo tarea",
    "tengo examen",
    "recuérdame algo",
    "haz una lista",
    "anota esto",
    "quiero enfocarme",
    "ayudame a estudiar",
    "pon una alarma",

    # EMOTIONAL
    "estoy triste",
    "me siento solo",
    "quiero llorar",
    "tengo ansiedad",
    "me siento mal",
    "estoy estresado",
    "me siento agotado",

    # SYSTEM
    "abre calculadora",
    "abre spotify",
    "abre navegador",
    "cierra ventana",
    "sube volumen",
    "baja volumen",
    "silencia la computadora",

    # TIME
    "que hora es",
    "que dia es hoy",
    "pon temporizador",
    "cronometro de 5 minutos",

    # FUN
    "cuentame un chiste",
    "di algo divertido",
    "hazme reir",
    "cuenta una historia",

    # NOTES
    "crear nota",
    "guarda esto",
    "escribe esto",
    "guardar recordatorio",
    "anota una idea"
]

vectorizer = CountVectorizer()

X = vectorizer.fit_transform(frases)

print(vectorizer.get_feature_names_out())

print(X.toarray())

labels = [

    "emergency","emergency","emergency","emergency",
    "emergency","emergency","emergency","emergency",

    "music","music","music","music",
    "music","music","music",

    "productivity","productivity","productivity","productivity",
    "productivity","productivity","productivity","productivity",

    "emotional","emotional","emotional","emotional",
    "emotional","emotional","emotional",

    "system","system","system","system",
    "system","system","system",

    "time","time","time","time",

    "fun","fun","fun","fun",

    "notes","notes","notes","notes","notes"
]

modelo = MultinomialNB()

modelo.fit(X, labels)

nuevo_texto = ["tengo que hacer tarea"]

nuevo_vector = vectorizer.transform(nuevo_texto)

prediccion = modelo.predict(nuevo_vector)

print(prediccion)

pruebas = [
    "necesito ayuda urgente",
    "pon musica relajante",
    "tengo examen mañana",
    "me siento triste",
    "abre calculadora",
    "que hora es",
    "cuentame un chiste",
    "crear nota"
]

for texto in pruebas:
    nuevo_vector = vectorizer.transform([texto])
    prediccion = modelo.predict(nuevo_vector)[0]
    probabilidades = modelo.predict_proba(nuevo_vector)[0]
    confianza = max(probabilidades)

    print("Texto:", texto)
    print("Intent:", prediccion)
    print("Confidence:", round(confianza, 2))
    print("-" * 30)