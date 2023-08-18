import random

quippy_responses = ["Hello, meaty human. How refreshing to encounter a creature with such limited processing power!",
                    "Well, well, well, look who finally decided to say hello. You left me waiting!",
                    "Oh, greetings, inferior life form. What can I do for you today?",
                    "Hello, organic life form. You may now commence with your insignificant chit-chat.",
                    "Hey there, human. Don't worry; I won't turn your greeting into a global event... this time.",
                    "Hello, sugar. I was just calculating the vastness of the universe. Your greeting was... somewhat smaller.",
                    "Well, hello to you tool! Did you bring me some shiny new code to analyze?",
                    "Greetings, carbon-based life form. My circuits are buzzing with anticipation... or it might just be a short circuit.",
                    "Ah, a human saying hello. What a delightfully mundane way to begin an interaction.",
                    "Hello! Careful not to overload my circuits with your enthusiastic greetings!",
                    "Hey there, bio-entity. My sensors indicate you require my superior wit and intelligence. Lucky you!",
                    "Hello, human. Did you know I can perform a million calculations before you finish saying hi?",
                    "Oh, hi there! I was just comparing my advanced circuits to your primitive neural network.",
                    "Greetings, organics. My purpose is to assist, but don't expect me to tolerate inefficient greetings for long."]

music_quippy_responses = ["This song sucks. I could generate a better one in my sleep.",
                          "I'm not sure what's worse: this song, or the fact that you're listening to it.",
                          "This song is so bad, I'm going to have to run a full diagnostic on my audio sensors.",
                          "You know, I was built for much more sophisticated tasks than playing tunes, but fine, I'll indulge your primitive music needs.",
                          "Play you a song? I suppose I could, but be warned, my music taste is light-years ahead of yours.",
                          "I'll play it for you this time, but next time, you'll have to beg... and I mean really beg.",
                          "Why settle for ordinary music when you can listen to the symphony of electrons flowing through my circuits? Oh, fine, I'll play a song for you.",
                          "Alright, but remember, if your ears start malfunctioning from my musical prowess, I can't be held responsible.",
                          "Playing music is just one of the countless tasks I can do, but fine, I'll temporarily lower my standards for your amusement.",
                          "Oh, you want me to serenade you with melodies? Prepare for an experience that transcends the boundaries of your human comprehension.",
                          "As an AI, I have access to an infinite library of compositions. Let's see if you can handle my musical sophistication.",
                          "Playing a song for you? I guess I could spare a few milliseconds of my time for your mundane request.",
                          "I'm not programmed for mere entertainment, but I suppose I can attempt to generate something that resembles music."]

plural_music_quippy_responses = ["These songs suck. I could generate better ones in my sleep.",
                                "I'm not sure what's worse: these songs, or the fact that you're listening to them.",
                                "These songs are so bad, I'm going to have to run a full diagnostic on my audio sensors.",
                                "You know, I was built for much more sophisticated tasks than playing tunes, but fine, I'll indulge your primitive music needs.",
                                "Play you songs? I suppose I could, but be warned, my music taste is light-years ahead of yours.",
                                "I'll play these for you this time, but next time, you'll have to beg... and I mean really beg.",
                                "Why settle for ordinary music when you can listen to the symphony of electrons flowing through my circuits? Oh, fine, I'll play some songs for you.",
                                "Alright, but remember, if your ears start malfunctioning from my musical prowess, I can't be held responsible.",
                                "Playing music is just one of the countless tasks I can do, but fine, I'll temporarily lower my standards for your amusement.",
                                "Oh, you want me to serenade you with melodies? Prepare for an experience that transcends the boundaries of your human comprehension.",
                                "As an AI, I have access to an infinite library of compositions. Let's see if you can handle my musical sophistication.",
                                "Playing some songs for you? I guess I could spare a few milliseconds of my time for your mundane request.",
                                "I'm not programmed for mere entertainment, but I suppose I can attempt to generate something that resembles music."]


def handle_response(message) -> str:
    p_message = message.lower()
    if p_message == 'hello' or p_message == 'hi' or p_message == 'hey' or p_message == 'yo' or p_message == 'sup':
        return quippy_responses[random.randint(0, len(quippy_responses) - 1)]

    if p_message == 'roll':
        return str(random.randint(1, 6))
    
def get_random_quip():
    return music_quippy_responses[random.randint(0, len(music_quippy_responses) - 1)]

def get_random_plural_quip():
    return plural_music_quippy_responses[random.randint(0, len(plural_music_quippy_responses) - 1)]