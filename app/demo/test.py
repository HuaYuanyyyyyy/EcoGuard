import requests

url = "https://onetoken.one/v1/images/generations/"
body = """{
  "prompt": "生成一只熊猫",
  "model": "gpt-image-2"
}"""
response = requests.request("POST", url, data = body, headers = {
  "Content-Type": "application/json", 
  "Authorization": "sk-nMorkI9vSXsNORHwtnNBTwB0WYk8wEEHi2KY5qTnhddbG2CH"
})

print(response.text)











