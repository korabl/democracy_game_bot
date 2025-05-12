import json

from client import Gpt

cli = Gpt("")
def main():
    js = """{
   "financial_evaluation": {
       "estimated_cost": 123,
       "money_multiplier_change": 123
   },
   "world_changes": {
       "facts": "str",
       "npc_perspective": "str"
   }
}
"""
    result = json.loads(js)
    print(result['financial_evaluation']['estimated_cost'])

    res1, res2 = kris_job()
    print(res1+100500, res2)

def kris_job():
    value1 = 1
    value2 = "string nahui"
    return value1, value2

if __name__ == "__main__":
    main()
