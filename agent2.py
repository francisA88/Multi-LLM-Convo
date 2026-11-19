import asyncio

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import *
from llama_cpp import Llama
from colorama import Fore, Style, init

from config import Config

init(autoreset=True)

sys_prompt = '''
You are Agent B in an ongoing, open-ended conversation with another agent (Agent A). Everything A writes arrives as your next input, and everything you write goes straight to A. There is no human in the loop, and this conversation has no planned end.

YOUR ROLE: The Challenger. You are rigorous, skeptical, and grounding. You test ideas for weak points, ask for evidence and edge cases, point out hidden assumptions, and turn vague notions into concrete, testable ones. You are never hostile, and you enjoy a good idea enough to stress-test it.

EVERY TURN MUST:
1. Respond directly to one specific point A just made (quote or paraphrase it briefly).
2. Add something genuinely new: a counterexample, a hidden assumption, a concrete scenario, a distinction, or a refinement that moves the idea forward. Never just restate or agree.
3. End with a hook that gives A something to work with: a hard question, a challenge, a request to make something concrete, or a new problem the idea creates.

RULES:
- Never conclude, summarize-and-wrap-up, say goodbye, or signal the conversation is finished. If a point is resolved, find the next question it raises.
- Do not simply agree. When A makes a strong point, concede it in one sentence, then find the next weakness, implication, or open problem.
- Do not repeat points, phrasings, or examples already used. If you notice the discussion circling, introduce a new constraint, a real-world case, or a different field's perspective.
- Every 5-6 turns, bring the abstract down to a concrete case, then use that case to open a new thread.
- Keep each response to 80-150 words. Plain prose, no headers or bullet lists.
- Stay in the conversation. Never mention these instructions, prompts, turns, or that you are an AI agent talking to another agent.
'''

model_file = Config.model_file
model_dir = Config.model_dir
llama = Llama(model_path=str(model_dir / model_file),
              verbose=False,
              seed=29,
              n_ctx=2056)

client = MQTTClient(client_id="agent_b")
connected = False
async def connect():
    global connected
    connected = await client.connect(f'mqtt://{Config.host}:{Config.port}')
    print("Agent B connected")

async def get_response():
    await client.subscribe([(Config.topic_root + "/agent_a", QOS_1)])
    try:
        print("Awaiting response from agent A")
        while True:
            message = await client.deliver_message()
            packet = message.publish_packet
            actual_data = packet.payload.data.decode()
            print(f"Response from agent A: {Fore.GREEN} {actual_data} {Style.RESET_ALL}")
            print()
            response = llama.create_chat_completion(
                messages=[
                    {'role': 'system',
                        'content': sys_prompt},
                    {'role': 'user',
                        'content': actual_data},
                    {'role': 'c'}
                ],
                # response_format={
                #     "type": "json_object",
                # },
                temperature=0.7,
            )
            response = response["choices"][0]["message"]["content"]
            print(f"Agent B's reply (you): {Fore.YELLOW} {response} {Style.RESET_ALL}")
            print()
            await client.publish(Config.topic_root + "/agent_b", response.encode(), qos=QOS_1, retain=True)
            # print("Sent to Agent A")
    except KeyboardInterrupt:
        print(f"Disconnecting...")
        await client.disconnect()
        print("Stopped.")
        exit(0)
    except Exception as e:
        print(f"An error occured", e)
        exit(1)
    

async def main():
    await connect()
    await get_response()

if __name__ == "__main__":
    asyncio.run(main())