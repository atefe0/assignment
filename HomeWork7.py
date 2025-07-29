import requests

def start_game():
    url = "https://mastermind.darkube.app/game"
    global game_id
    game_id = requests.post(url)
    game_id = game_id.json().get("game_id")
    return game_id

def send_guess(game_id, guess):
    url = "https://mastermind.darkube.app/guess"
    global response
    response = requests.post(url, json={"game_id":game_id,"guess":guess})
    print(f"your guess:{guess}")
    print(f"status:{response.status_code}")
    return response

def valid_guess(guess):
   if len(guess) == 4 and len(set(guess)) == 4 and guess.isdigit() and all(i in "123456" for i in guess):
        return True 
   else:
       return False

def prompt_guess(game_id):
    while True:
        guess = input("Enter your guess(1-6 and no repeats):")
        if not valid_guess(guess):
            print("Invalid guess. Try again.")
            continue
        result = send_guess(game_id, guess).json()
        if result is None:
            print("server did not respond.")
        white = result["white"]
        black = result["black"]
        print(f"correct digit in wrong place:{white}")
        print(f"correct digit in correct place:{black}")
        if black == 0 and white == 0:
            print("None of your guesses was correct.")
            continue
        if black == 4:
            print("You won.")
            break

def run_game():
    print("Welcome to Mastermind.")
    game_id = start_game()
    if game_id:
        prompt_guess(game_id)

if __name__ == "__main__":
    run_game()

