import os
import random
import uuid
from typing import Dict, Any
import openai
from .utils import get_openai_api_key, read_txt_file, text_to_speech_s3, save_json_to_s3, load_json_from_s3, upload_image_to_s3

openai.api_key = get_openai_api_key()
REGION = os.environ.get('REGION')
OPENAI_MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.85
TOP_P = 0.75
MAX_LEN = 1024
MAX_INPUT_LEN = 5000
CHEFS = [i.split(".txt")[0] for i in os.listdir("src/roasts")]
CHEFS_ROAST = {chef.lower(): read_txt_file(f"src/roasts/{chef.lower()}.txt") for chef in CHEFS}
CHEFS_ROAST_ALL = "\n\n".join(CHEFS_ROAST.values())
S3_BUCKET = os.environ.get('BUCKET_NAME')


def create_image(prompt: str) -> str:
    """
    Generates an image based on the provided prompt using OpenAI's DALL-E model.

    Args:
        prompt (str): The text prompt to generate the image.

    Returns:
        str: The URL of the generated image.
    """
    response = openai.Image.create(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    print(f"Created Image with #{prompt}# with URL: {image_url}!")

    return image_url


def openai_guess_the_chef_name(user_message: str, descriptions: str) -> str:
    """
    Uses OpenAI's API to guess the chef's name based on user input and descriptions.

    Args:
        user_message (str): The user's input message.
        descriptions (str): Descriptions of the persons.

    Returns:
        str: The guessed chef's name or an error message.
    """
    prompt = (
        f"Persons Descriptions:\n{descriptions}\n"
        f"User input: {user_message}\n"
        "Based on the user input and the descriptions of the persons above, "
        "guess who the input is about. NO MATTER WHAT, ONLY output their name without anything before or after it."
    )

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_LEN,
            n=1,  # Number of responses to generate
            stop=None  # Define stop sequences if needed
        )
        # Extract and clean the response text
        response_text = response.choices[0].message.content.strip()
        return response_text
    except openai.error.OpenAIError as e:
        return f"Error communicating with OpenAI: {str(e)}"


def openai_get_the_roast(user_message: str, chef_to_roast: str, descriptions: str) -> str:
    """
    Uses OpenAI's API to generate a roast for the specified chef.

    Args:
        user_message (str): The user's input message.
        chef_to_roast (str): The name of the chef to roast.
        descriptions (str): Descriptions of the chef.

    Returns:
        str: The generated roast or an error message.
    """
    prompt = (
        f"DataChef Roasting Party!\n\n"
        f"Here's the next person: {chef_to_roast}. The input message: {user_message}. Some information about them:\n{descriptions}\n\n"
        f"Your task: Roast {chef_to_roast}. RANDOMLY Pick just one thing from the description to focus on, "
        "and deliver the FUNNIEST, most savage roast you can. Keep it FUNNY, and SPICY. Avoid Politics. "
        "DO NOT try to use everything in the description, PICK ONLY ONE thing and go all in. "
        "ONLY GIVE ME THE ROAST, NOTHING ELSE!"
    )

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_LEN,
            n=1,  # Number of responses to generate
            stop=None  # Define stop sequences if needed
        )
        # Extract and clean the response text
        response_text = response.choices[0].message.content.strip()
        return response_text
    except openai.error.OpenAIError as e:
        return f"Error communicating with OpenAI: {str(e)}"


def openai_get_reasoning(user_message: str, chef_description: str, chef: str, random: bool) -> str:
    """
    Uses OpenAI's API to generate the reason why the chef is chosen.

    Args:
        user_message (str): The user's input message.
        chef_description (str): Descriptions of the chef.
        chef (str): The name of the chef.
        random (bool): Whether the chef is randomly chosen.
    Returns:
        str: The guessed chef's name or an error message.
    """
    prompt = (
        f"User input: {user_message}\n"
        f"Based on the user input and the descriptions of chefs we have guessed the user input is referring to {chef}\n"
        f"These are some details about {chef}: {chef_description}\n"
        f"Now you have to generate some reasoning step that why we chose {chef}. The reasoning should be logical and "
        f"related to user input but SHOULD NOT directly mention the chef, we want to make it engaging\n"
        f"Make sure to keep it VERY VERY SHORT and do NOT mention {chef} in it!"
    )
    if random:
        prompt += ("Start with 'Lets roast some chef with ... characteristics' like: let's roast a boy in tech world,"
                   " or let's roast a girl in dutch culture ...\nGive a VERY VERY SHORT result with just a few words")
    else:
        prompt += ("Start with 'I think' like: I think it should be a boy in tech, "
                   "or I think it's a girl with dutch culture ...\nGive a SHORT result with a few words")

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=128,
            n=1,  # Number of responses to generate
            stop=None  # Define stop sequences if needed
        )
        # Extract and clean the response text
        response_text = response.choices[0].message.content.strip()
        return response_text
    except openai.error.OpenAIError as e:
        return f"Error communicating with OpenAI: {str(e)}"


def check_and_handle_miss_guessed_chef(guessed_chef: str) -> str:
    """
    Checks if the guessed chef exists in the list of chefs and handles mismatches.

    Args:
        guessed_chef (str): The name of the guessed chef.
        chefs (list, optional): List of valid chef names. Defaults to CHEFS.

    Returns:
        str: A valid chef name, either the correctly guessed name or a random chef.
    """
    lower_chefs = [i.lower() for i in CHEFS]
    if guessed_chef.lower() in lower_chefs:
        return guessed_chef.lower()
    else:
        print("Guess Randomly")
        return random.choice(CHEFS).lower()


def find_chef(request: Dict[str, Any]) -> Dict[str, str]:
    """
    Identifies the chef based on the user message and provides a reasoning.

    Args:
        request (Dict[str, Any]): The request containing the user prompt.

    Returns:
        Dict[str, str]: A dictionary with the guessed chef's name and the reasoning.
    """
    user_message = request['prompt']
    if len(user_message) >= MAX_INPUT_LEN:
        user_message = request['prompt'][:MAX_INPUT_LEN]

    if user_message != "":
        guessed_chef = openai_guess_the_chef_name(user_message=user_message, descriptions=CHEFS_ROAST_ALL)
        guessed_chef = check_and_handle_miss_guessed_chef(guessed_chef)
        
        reason = openai_get_reasoning(
            user_message=user_message, chef_description=CHEFS_ROAST[guessed_chef], chef=guessed_chef, random=False
        )
    else:
        # choose randomly
        guessed_chef = check_and_handle_miss_guessed_chef("")
        reason = openai_get_reasoning(
            user_message=user_message, chef_description=CHEFS_ROAST[guessed_chef], chef=guessed_chef, random=True
        )

    roast_id = uuid.uuid4().hex

    if request['muted']:
        audio_s3_url = None
    else:
        s3_key = f"results/audio/{roast_id}-guess.mp3"
        audio_s3_url = text_to_speech_s3(reason, s3_key, expiration=604800)

    return {"name": guessed_chef, "reason": reason, 'audio_url': audio_s3_url, "roast_id": roast_id}


def roast_chef(request: Dict[str, str]) -> Dict[str, str]:
    """
    Generates a roast for the specified chef based on the user message.

    Args:
        request (Dict[str, str]): A dictionary containing the user message and the chef's name.

    Returns:
        Dict[str, str]: A dictionary with the chef's name and the generated roast.
    """
    user_message = request['prompt']
    guessed_chef = request['chef']

    roast = openai_get_the_roast(
        user_message=user_message, chef_to_roast=guessed_chef, descriptions=CHEFS_ROAST[guessed_chef]
    )
    roast_id = request['roast_id']

    if request['muted']:
        roast_audio_s3_url = None
    else:
        roast_audio_s3_url = text_to_speech_s3(roast, f"results/audio/{roast_id}.mp3", expiration=604800)

    result = {
        "name": guessed_chef, "roast": roast, "roast_id": roast_id,
        "roast_audio_s3_url": roast_audio_s3_url, "audio_key": f"results/audio/{roast_id}.mp3"
    }
    save_json_to_s3(f"results/roasts/{roast_id}.json", result)
    return result


def generate_roast_image_url(request: Dict[str, str]) -> Dict[str, str]:
    """
    Generates an image URL based on the roast text.

    Args:
        request (Dict[str, str]): A dictionary containing the roast text.

    Returns:
        Dict[str, str]: A dictionary with the generated image URL.
    """
    roast = request['roast']

    roast_image_url = create_image(roast)
    roast_id = request['roast_id']
    image_url = upload_image_to_s3(roast_image_url, f"results/images/{roast_id}.jpg")

    result = load_json_from_s3(f"results/roasts/{roast_id}.json")
    result['image_key'] = f"results/images/{roast_id}.jpg"
    save_json_to_s3(f"results/roasts/{roast_id}.json", result)

    return {"roast_image_url": image_url}
