import os
import requests
import json

SCORE_SUCCESSFUL_MINT = 40
SCORE_SUCCESSFUL_TRANSFER =40

feedbackRes = []

def send_feedback(score, msg):
    post = {'fractionalScore': score, 'feedback': msg}
    # Optional: this goes to container log and is best practice for debugging purpose
    print(json.dumps(post))
    # This is required for actual feedback to be surfaced
    with open(os.getenv('OUTPUT_PATH'), "w") as outfile:
        json.dump(post, outfile)


def get_transactions_by_address(contract_address, decentralized_id, api_key,beneficiary_address):
    is_token_minted = is_transfered = False
    url = "https://api-sepolia.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "contractAddress": contract_address,
        "address":decentralized_id,
        "page": 1,
        "offset":100,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    temp  = response.json()
    print("resp",temp)

    if response.status_code == 200:
        for transaction in temp['result']:
            print()
            print("Block Number:", transaction["blockNumber"])
            print("From:", transaction["from"])
            print("To:", transaction["to"])
            print("Token Symbol:", transaction["tokenSymbol"])

            if not is_token_minted:
                mint_conditions = (
                    transaction["from"] == "0x0000000000000000000000000000000000000000",
                    transaction["to"].lower() == decentralized_id.lower(),
                    transaction["tokenSymbol"].lower() == transaction["tokenSymbol"].lower(),
                    transaction["tokenName"].lower() == transaction["tokenName"].lower()
                )
                if all(mint_conditions):
                    is_token_minted = True

            if not is_transfered:
                result = float(transaction["value"])
                token_value = result // 10 ** 18

                print("Transferred Token Value:", token_value)
                print("benef:", beneficiary_address.lower())
                print("tran:", transaction["to"].lower())
                print("res",transaction["to"].lower() == beneficiary_address.lower())


                transfer_conditions = (
                    transaction["from"].lower() == decentralized_id.lower(),
                    transaction["to"].lower() == beneficiary_address.lower(),
                    transaction["tokenSymbol"].lower() == transaction["tokenSymbol"].lower(),
                    transaction["tokenName"].lower() == transaction["tokenName"].lower(),
                    token_value > 0
                )
                if all(transfer_conditions):
                    is_transfered = True

            if is_token_minted and is_transfered:
                break

        print("Is Mint Operation performed on ERC20 Token : " + str(is_token_minted));
        print("Is Transaction Operation performed on ERC20 Token : " + str(is_transfered));

        score = 0
        map = {}

        if (is_token_minted):
            score += 40;
            map["MINT_TOKEN"]= 40
            if (is_transfered):
                score += 40
                map["TOKEN_TRANSFER"]=40

                print("Map [Score : Transfer and Mint] : " + map);

                return map
        return response.json()
    else:
        return None
		
			

def isMinted(contract_address: str, decentralized_id: str, api_key: str) -> int:
    """Function to check if the token is minted."""
    url = "https://api-sepolia.etherscan.io/api"

    params = {
        "module": "account",
        "action": "tokentx",
        "contractAddress": contract_address,
        "address":decentralized_id,
        "page": 1,
        "offset":100,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad status codes
        transactions = response.json()

        print("Status Code:", response.status_code)
        print("Status Code:", transactions)
        minted = any(transaction["contractAddress"].lower() == contract_address.lower() and 
                     transaction["to"].lower() == decentralized_id.lower() for transaction in transactions.get("result", []))
        if minted:
            return SCORE_SUCCESSFUL_MINT
        else:
            return 0
    except requests.exceptions.RequestException as err:
        print(f'Error occurred during request: {err}')
        return 0

def isTransferred(decentralized_id: str, beneficiary_address: str, api_key: str) -> int:
    """Function to check if the token is transferred."""
    url = "https://api-sepolia.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokennfttx",
        "contractAddress": contract_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }
    try:
        response = requests.get(url, params=params)
        print("Status Code:", response.status_code)
        response.raise_for_status()  # Raise an HTTPError for bad status codes
        print("y")
        transactions = response.json()
        print("here")
        print("tx", transactions)
        transferred = any(transaction["from"].lower() == decentralized_id.lower() and
                         transaction["to"].lower() == beneficiary_address.lower() for transaction in transactions.get("result", []))
        if transferred:
            return SCORE_SUCCESSFUL_TRANSFER
        else:
            return 0
    except requests.exceptions.RequestException as err:
        print(f'Error occurred during request: {err}')
        return 0



def init(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    contract_address = decentralized_id = beneficiary_address = None
    for line in lines:
        if "contract_address" in line:
            contract_address = line.split('=')[1].strip().replace('"', '')
        elif "decentralized_id" in line:
            decentralized_id = line.split('=')[1].strip().replace('"', '')
        elif "beneficiary_address" in line:
            beneficiary_address = line.split('=')[1].strip().replace('"', '')

    if(beneficiary_address and decentralized_id and beneficiary_address):
        return contract_address, decentralized_id, beneficiary_address
    raise RuntimeError

api_key = "4WT5YN9UASF77UJ2ZV5KF25B8IKES3C1K5"
SEPOLIA_URL = "https://api-sepolia.etherscan.io/api?"


#file_path = os.getenv('USER_FILE_PATH')

contract_address, decentralized_id, beneficiary_address ="0xb1AC9E086381e22adB6B36A211c3517f18CAc200","0x1dF4E224E016DB06e25d27120c0BD333617E6Fc3","0x6aa85B820ea3fA061CA5831DcD47De7Bc888324C"

transactions = get_transactions_by_address(contract_address, decentralized_id,api_key ,beneficiary_address)
#isMinted(transactions, contract_address, decentralized_id),
print(transactions)
if not transactions:
    scores = [
        
        isMinted(contract_address, decentralized_id,api_key),
		isTransferred(transactions, contract_address, decentralized_id)
        
    ]

    total = 0
    for j in range(len(scores)):
        total += scores[j]

    separator = " "
    send_feedback(total / 100, separator.join(feedbackRes))