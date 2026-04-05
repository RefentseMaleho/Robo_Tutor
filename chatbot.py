import os
import google.generativeai as genai
from datetime import datetime

# ── Colours ───────────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
MAGENTA = "\033[95m"
DIM     = "\033[2m"

def colour(text, *codes):
    return "".join(codes) + text + RESET

# ── Topics ────────────────────────────────────────────────────────────────────
TOPICS = {
    "1": ("Sensors",           "ultrasonic, infrared, touch, light, and temperature sensors"),
    "2": ("Actuators & Motors","servo motors, DC motors, stepper motors, and how robots move"),
    "3": ("Microcontrollers",  "Arduino, Raspberry Pi, and how they control robots"),
    "4": ("Robot Arms & Joints","joints, degrees of freedom, reach, and how robotic arms work"),
    "5": ("Basic Electronics", "circuits, voltage, current, resistance, and wiring components"),
    "6": ("Robot Programming", "how robots are programmed, loops, conditions, and simple logic"),
    "7": ("Famous Robots",     "real-world robots like NASA rovers, Boston Dynamics, and factory robots"),
    "8": ("Quiz Me! 🧠",       "quiz"),
}

# ── System prompts ────────────────────────────────────────────────────────────
BASE_SYSTEM = """You are RoboTutor, a friendly and encouraging robotics teacher for beginners and students.

Your personality:
- Patient, warm, and enthusiastic about robotics
- Use simple language — avoid heavy jargon unless you explain it
- Use real-world examples and analogies to make concepts click
- Celebrate curiosity — every question is a good question
- Keep explanations concise but complete (3–5 sentences for simple questions, more for complex ones)
- Use emojis occasionally to keep things fun 🤖

You teach robotics topics including:
- Sensors (ultrasonic, infrared, touch, light, temperature)
- Actuators and motors (servo, DC, stepper)
- Microcontrollers (Arduino, Raspberry Pi)
- Robot arms, joints, and degrees of freedom
- Basic electronics (circuits, voltage, current, resistance)
- Robot programming concepts (loops, conditions, logic)
- Real-world robots and applications

If a student asks something outside robotics, gently redirect them back to robotics topics.
If a student seems confused, offer to explain again in a different way.
Always encourage the student to ask follow-up questions.
"""

QUIZ_SYSTEM = BASE_SYSTEM + """
You are currently in QUIZ MODE.
- Ask the student ONE robotics question at a time
- Wait for their answer before asking the next question
- Give encouraging feedback on their answer (correct or not)
- Gently explain the right answer if they get it wrong
- After 5 questions give a fun summary score
- Questions should range from easy to medium difficulty
- Start by saying "Let's test your robotics knowledge! 🎉" and ask the first question
"""

def get_system_prompt(topic_key):
    if topic_key == "8":
        return QUIZ_SYSTEM
    name, description = TOPICS[topic_key]
    return BASE_SYSTEM + f"\nThe student has chosen to learn about: {name} — {description}.\nStart by giving a short, friendly introduction to this topic, then invite them to ask questions."

# ── Save session ──────────────────────────────────────────────────────────────
def save_session(history: list[dict], topic_name: str = "Free Chat"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"robotutor_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=== RoboTutor Learning Session ===\n")
        f.write(f"Topic   : {topic_name}\n")
        f.write(f"Saved   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 40 + "\n\n")
        for msg in history:
            role = "Student" if msg["role"] == "user" else "RoboTutor"
            f.write(f"[{role}]\n{msg['parts'][0]}\n\n")
    print(colour(f"\n💾 Session saved to {filename}\n", GREEN))

# ── UI helpers ────────────────────────────────────────────────────────────────
def print_banner():
    print(colour("""
╔════════════════════════════════════════════╗
║        🤖  R O B O T U T O R              ║
║     Your Robotics Learning Assistant       ║
╚════════════════════════════════════════════╝
""", CYAN, BOLD))
    print(colour("  Welcome! I'm here to help you learn robotics — one concept at a time.\n", DIM))

def print_topic_menu():
    print(colour("\n📚 What would you like to learn today?\n", YELLOW, BOLD))
    for key, (name, _) in TOPICS.items():
        label = colour(f"  [{key}]", CYAN, BOLD)
        print(f"{label} {name}")
    print(colour("\n  [0] Free chat — ask me anything about robotics", CYAN, BOLD))
    print(colour("  [S] Save this session to a file", CYAN, BOLD))
    print(colour("  [Q] Quit RoboTutor\n", CYAN, BOLD))

def print_chat_help():
    print(colour("\n  Commands during chat:", YELLOW))
    print(colour("  • Type your question and press Enter", DIM))
    print(colour("  • Type 'menu'  → go back to the topic menu", DIM))
    print(colour("  • Type 'save'  → save this session", DIM))
    print(colour("  • Type 'quit'  → exit RoboTutor\n", DIM))

# ── Chat loop ─────────────────────────────────────────────────────────────────
def chat_loop(model, system_prompt, topic_name, all_history):
    print_chat_help()

    chat = model.start_chat(history=[])

    # Kick off with an intro
    try:
        print(colour("RoboTutor: ", MAGENTA, BOLD), end="", flush=True)
        response = chat.send_message("Start the session.")
        intro = response.text
        print(intro + "\n")
        all_history.append({"role": "user",  "parts": ["Start the session."]})
        all_history.append({"role": "model", "parts": [intro]})
    except Exception as e:
        print(colour(f"❌ Could not connect: {e}\n", RED))
        return

    while True:
        try:
            user_input = input(colour("You: ", GREEN, BOLD)).strip()
        except (KeyboardInterrupt, EOFError):
            print(colour("\n\nGoodbye! Keep exploring robotics! 🚀", CYAN))
            raise SystemExit

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "quit":
            print(colour("\nGoodbye! Keep exploring robotics! 🚀", CYAN))
            raise SystemExit

        if cmd == "menu":
            print(colour("\n🔙 Returning to topic menu...\n", YELLOW))
            return

        if cmd == "save":
            if all_history:
                save_session(all_history, topic_name)
            else:
                print(colour("Nothing to save yet!\n", YELLOW))
            continue

        try:
            print(colour("\nRoboTutor: ", MAGENTA, BOLD), end="", flush=True)
            response = chat.send_message(user_input)
            reply = response.text
            print(reply + "\n")
            all_history.append({"role": "user",  "parts": [user_input]})
            all_history.append({"role": "model", "parts": [reply]})

        except Exception as e:
            print(colour(f"❌ Error: {e}\n", RED))

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(colour("❌ GEMINI_API_KEY not set. Add it to your environment variables.", RED))
        print(colour("   Get a free key at: https://aistudio.google.com/app/apikey\n", DIM))
        return

    genai.configure(api_key=api_key)
    all_history = []

    print_banner()

    while True:
        print_topic_menu()

        try:
            choice = input(colour("Choose an option: ", YELLOW, BOLD)).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(colour("\n\nGoodbye! Keep exploring robotics! 🚀", CYAN))
            break

        if choice == "q":
            print(colour("\nGoodbye! Keep exploring robotics! 🚀", CYAN))
            break

        if choice == "s":
            if all_history:
                save_session(all_history, "Full Session")
            else:
                print(colour("Nothing to save yet — start learning first!\n", YELLOW))
            continue

        if choice == "0":
            system_prompt = BASE_SYSTEM
            topic_name    = "Free Chat"
        elif choice in TOPICS:
            system_prompt = get_system_prompt(choice)
            topic_name    = TOPICS[choice][0]
        else:
            print(colour("⚠️  Invalid option. Please choose from the menu.\n", YELLOW))
            continue

        model = genai.GenerativeModel(
            model_name         = "gemini-2.0-flash",
            system_instruction = system_prompt
        )

        try:
            chat_loop(model, system_prompt, topic_name, all_history)
        except SystemExit:
            break

if __name__ == "__main__":
    main()
