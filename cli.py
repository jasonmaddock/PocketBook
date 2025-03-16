import argparse

from adding_accounts import generate_bank_list, add_account, list_accounts, get_balances_and_transactions

def main():
    parser = argparse.ArgumentParser(description = "PocketBook")
    
    parser.add_argument("-l", "--list_banks")
    parser.add_argument("-a", "--add_bank")
    parser.add_argument("-s", "--show_accounts")
    parser.add_argument("-b", "--balance_transactions")

    args = parser.parse_args()

    if args.list_banks != None:
        country_code = args.list_banks
        banks = generate_bank_list(country_code)
        for bank in banks:
            print(bank["name"], bank["id"])
    
    elif args.add_bank != None:
        bank_name = args.add_bank
        for bank in generate_bank_list():
            if bank["name"] == bank_name:
                return add_account(bank["id"])
        print("Bank not found")
    
    elif args.show_accounts != None:
        print(list_accounts())

    elif args.balance_transactions != None:
        accounts = list_accounts()
        print(get_balances_and_transactions(accounts))



        
if __name__ == "__main__":
    # calling the main function
    main()

accounts = list_accounts()
print(get_balances_and_transactions(accounts))
