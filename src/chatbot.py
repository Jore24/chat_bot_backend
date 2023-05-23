import re
import random

def get_response(user_input):
    split_message = re.split(r'\s|[,:;.?!-_]\s*', user_input.lower())
    response = check_all_messages(split_message)

    if user_input == 'Soporte':
        response = 'Te vamos redirigir con un agente de soporte'

    elif response == '¿En qué distrito te encuentras?':
        response = '¿En qué distrito te encuentras? XD??'
    districts = ['Lima', 'SJL', 'Miraflores', 'San Isidro', 'Surco', 'Barranco']  
    if user_input in districts:
        if user_input == 'Lima':
            response = 'Nuestra sucursal en el distrito de '+user_input+ ' se encuentra ubicada en la Av. Javier Prado Este '
        elif user_input == 'SJL':
            response = 'Nuestra sucursal en el distrito de '+user_input+ ' se encuentra ubicada en la Av. Javier Prado Este '

            
    return response


def message_probability(user_message, recognized_words, single_response=False, required_words=[]):
    message_certainty = 0
    has_required_words = True

    for word in user_message:
        if word in recognized_words:
            message_certainty +=1

    percentage = float(message_certainty) / float (len(recognized_words))

    for word in required_words:
        if word not in user_message:
            has_required_words = False
            break

    if has_required_words or single_response:
        return int(percentage * 100)
    else:
        return 0


def check_all_messages(message):
    highest_prob = {}

    def response(bot_response, list_of_words, single_response=False, required_words=[]):
        nonlocal highest_prob
        if single_response:
            highest_prob[bot_response] = message_probability(message, list_of_words, single_response, required_words)
        else:
            for word in list_of_words:
                if word in message:
                    highest_prob[bot_response] = message_probability(message, list_of_words, single_response, required_words)
                    break

    response('Hola, ¿en qué puedo ayudarte?', ['hola', 'klk', 'saludos', 'buenas'], single_response=True)
    response('Soporte', ['Otros', 'Soporte', 'Atención al cliente'], single_response=True)
    response('¿En qué distrito te encuentras?', ['sucursal', 'dónde', 'distrito', 'ubicación'], single_response=True)
    response('Ofrecemos una amplia gama de servicios de envío y logística', ['servicios', 'envío', 'logística'], single_response=True)
    response('Gracias por contactarnos, estaremos aquí para ayudarte', ['exit', 'bye', 'chau'], single_response=True)
   
    best_match = max(highest_prob, key=highest_prob.get)

    return unknown() if highest_prob[best_match] < 1 else best_match

def unknown():
    responses = [
        "Disculpa, no estoy seguro de entender. ¿Podrías reformular tu pregunta?",
        "Me gustaría poder ayudarte, pero necesito más información. ¿Puedes proporcionar más detalles?",
        "No tengo la respuesta exacta en este momento, pero puedo intentar ayudarte con otra pregunta. ¿En qué más puedo asistirte?",
        "¡Ups! Parece que estoy un poco confundido. ¿Puedes plantear tu pregunta de otra manera?",
        "Lo siento, no tengo la respuesta en este momento. ¿Hay algo más en lo que pueda ayudarte?",
        "No estoy seguro de lo que quieres decir. ¿Podrías explicarlo de manera diferente?"
    ]
    
    return random.choice(responses)

def run_chatbot():
    while True:
        user_input = input('You: ')
        if user_input.lower() == 'adios':
            print('Bot: ¡Hasta luego!')
            break
        else:
            print('Bot: ' + get_response(user_input))
