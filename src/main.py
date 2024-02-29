import os
import requests
import json

SCORE_SUCCESSFULL_TOKEN_BALANCE = 20
SCORE_SUCCESSFUL_MINT = 40
SCORE_SUCCESSFUL_TRANSFER =40
total = 0
feedbackRes = []
scores_map = {}
def send_feedback(score, msg):
    post = {'fractionalScore': score, 'feedback': msg}
    # Optional: this goes to container log and is best practice for debugging purpose
    print(json.dumps(post))
    # This is required for actual feedback to be surfaced
    with open(os.getenv('OUTPUT_PATH'), "w") as outfile:
        json.dump(post, outfile)


def get_tokenbalance_by_address(api_key, address, decentralised_id):
    url = "https://api-sepolia.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractAddress": address,
        "address": decentralised_id,
        "tag": "latest",
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def calculateTokenBalanceScore(transactions):
    trxs = json.loads(json.dumps(transactions))
    if(int(trxs["result"]) <= 0):
       feedbackRes.append("You lost 20 points for not meeting the TOKEN_BALANCE requirement. Please make sure that you (the owner) has sufficient token supply.")
       return
    feedbackRes.append("You gained 20 points for meeting the TOKEN_BALANCE requirement.")
    scores_map["TOKEN_BALANCE"] = SCORE_SUCCESSFULL_TOKEN_BALANCE

def get_transactions_by_address(contract_address, decentralized_id, token_name, token_symbol, api_key):
    
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
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as err:
        print(f'Error occurred during request: {err}')
        return None

def checkMintingAndTokenTransfer(transactions, decentralized_id ,beneficiary_address):
    is_token_minted = is_transfered = False
    print("transaction: ", transactions)
    if transactions["message"] == "OK":
        for transaction in transactions['result']:
            print("ALL")
            print("Block Number:", transaction["blockNumber"])
            print("From:", transaction["from"])
            print("To:", transaction["to"])
            print("Token Symbol:", transaction["tokenSymbol"])

            if not is_token_minted:
                mint_conditions = (
                    transaction["from"] == "0x0000000000000000000000000000000000000000",
                    transaction["to"].lower() == decentralized_id.lower(),
                    transaction["tokenSymbol"].lower() == token_symbol.lower(),
                    transaction["tokenName"].lower() == token_name.lower()
                )
                if all(mint_conditions):
                    is_token_minted = True

            if not is_transfered:
                result = float(transaction["value"])
                token_value = result
                # print("TRANSFER")
                # print("Transferred Token Value:", token_value)
                # print("benef:", beneficiary_address.lower())
                # print("tran:", transaction["to"].lower())
                # print("res",transaction["to"].lower() == beneficiary_address.lower())


                transfer_conditions = (
                    transaction["from"].lower() == decentralized_id.lower(),
                    transaction["to"].lower() == beneficiary_address.lower(),
                    transaction["tokenSymbol"].lower() == token_symbol.lower(),
                    transaction["tokenName"].lower() == token_name.lower(),
                    token_value > 0
                )
                if all(transfer_conditions):
                    is_transfered = True

            if is_token_minted and is_transfered:
                break

        print("Is Mint Operation performed on ERC20 Token : " + str(is_token_minted))
        print("Is Transaction Operation performed on ERC20 Token : " + str(is_transfered))


        if (is_token_minted):
            scores_map["MINT_TOKEN"] = SCORE_SUCCESSFUL_MINT
            feedbackRes.append("You gained 40 points for meeting mint token requirement.")
        else:
            feedbackRes.append("You lost 40 points for not meeting mint token requirement.")

        if (is_transfered):
            scores_map["TOKEN_TRANSFER"] = SCORE_SUCCESSFUL_TRANSFER
            feedbackRes.append("You gained 40 points for meeting transfer token requirement.")
        else:
            feedbackRes.append("Transfer function not implemented as per requirements. Refer to the handout. Lost 40 points for Transfer Token.")

        print("scores_map [Score : Transfer and Mint] : " + str(scores_map.values()))

    else:
        feedbackRes.append("You lost 40 points for not meeting mint token requirement.")
        feedbackRes.append("Transfer function not implemented as per requirements. Refer to the handout. Lost 40 points for Transfer Token.")



def init(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    contract_address = decentralized_id = beneficiary_address = token_name = token_symbol = None
    for line in lines:
        if "contract_address" in line:
            contract_address = line.split('=')[1].strip().replace('"', '')
        elif "decentralized_id" in line:
            decentralized_id = line.split('=')[1].strip().replace('"', '')
        elif "beneficiary_address" in line:
            beneficiary_address = line.split('=')[1].strip().replace('"', '')
        elif "token_name" in line:
            token_name = line.split('=')[1].strip().replace('"', '')            
        elif "token_symbol" in line:
            token_symbol = line.split('=')[1].strip().replace('"', '')


    if(beneficiary_address and decentralized_id and beneficiary_address and token_name and token_symbol):
        return contract_address, decentralized_id, beneficiary_address, token_name, token_symbol
    raise RuntimeError

api_key = "4WT5YN9UASF77UJ2ZV5KF25B8IKES3C1K5"
SEPOLIA_URL = "https://api-sepolia.etherscan.io/api?"
initializations = 1
alphanumcheck = 1
try:
    file_path = os.getenv('USER_FILE_PATH')
    if not file_path:
        raise ValueError("Environment variable 'USER_FILE_PATH' not set")

    contract_address, decentralized_id, beneficiary_address, token_name, token_symbol = init(file_path)
    balance_transactions = get_tokenbalance_by_address(api_key, contract_address, decentralised_id=decentralized_id)
    transactions = get_transactions_by_address(contract_address, decentralized_id, token_name, token_symbol, api_key)
except:
    initializations = 0
    feedbackRes.append("Error while grading! Please contact the support!")

if  initializations and not (contract_address.isalnum() and decentralized_id.isalnum() and beneficiary_address.isalnum()):
    alphanumcheck = 0
    feedbackRes.append("Only alphaneumeric values are valid for token/contract/wallet addresses.")
    

if initializations and alphanumcheck and transactions and balance_transactions:
    calculateTokenBalanceScore(balance_transactions)
    checkMintingAndTokenTransfer(transactions, decentralized_id ,beneficiary_address)
    scores = [
       scores_map.get("TOKEN_BALANCE", 0),
       scores_map.get("MINT_TOKEN", 0),
       scores_map.get("TOKEN_TRANSFER", 0)
    ]

    for key, val in scores_map.items():
        total += val

separator = " "
send_feedback(total / 100, separator.join(feedbackRes))