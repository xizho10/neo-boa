"""
NEP5 Token
===================================

This file, when compiled to .avm format, would comply with the current NEP5 token standard on the NEO blockchain

Token standard is available in proposal form here:
`NEP5 Token Standard Proposal <https://github.com/neo-project/proposals/blob/master/nep-5.mediawiki>`_

Compilation can be achieved as such

>>> from boa.compiler import Compiler
>>> Compiler.load_and_save('./boa/tests/src/NEP5Test.py')


Below is the current implementation in Python


"""

from boa.blockchain.vm.Neo.Runtime import Log, Notify
from boa.blockchain.vm.System.ExecutionEngine import GetScriptContainer, GetExecutingScriptHash
from boa.blockchain.vm.Neo.Transaction import *
from boa.blockchain.vm.Neo.Blockchain import GetHeight, GetHeader
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import GetTrigger, CheckWitness
from boa.blockchain.vm.Neo.TriggerType import Application, Verification
from boa.blockchain.vm.Neo.Output import GetScriptHash, GetValue, GetAssetId
from boa.blockchain.vm.Neo.Storage import GetContext, Get, Put, Delete
from boa.code.builtins import concat

# -------------------------------------------
# TOKEN SETTINGS
# -------------------------------------------

TOKEN_NAME = 'NEP5 Standard'
SYMBOL = 'NEP5'

# Script hash of the contract owner
OWNER = b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5'

# Number of decimal places
DECIMALS = 8

# Total supply of tokens
TOTAL_SUPPLY = 500000000000000


# -------------------------------------------
# Events
# -------------------------------------------

OnTransfer = RegisterAction('transfer', 'from', 'to', 'amount')

OnApprove = RegisterAction('approval', 'owner', 'spender', 'value')


def Main(operation, args):

    """
    This is the main entry point for the Smart Contract

    :param operation: the operation to be performed ( eg `mintTokens`, `transfer`, etc)
    :type operation: str

    :param args: an optional list of arguments
    :type args: list

    :return: indicating the successful execution of the smart contract
    :rtype: bool
    """

    trigger = GetTrigger()

    if trigger == Verification():


        is_owner = CheckWitness(OWNER)

        if is_owner:

            return True

        return False

    elif trigger == Application():

        if operation == 'name':
            n = TOKEN_NAME
            return n

        elif operation == 'decimals':
            d = DECIMALS
            return d

        elif operation == 'symbol':
            sym = SYMBOL
            return sym

        elif operation == 'totalSupply':
            supply = TOTAL_SUPPLY
            return supply

        elif operation == 'balanceOf':
            if len(args) == 1:
                account = args[0]
                balance = BalanceOf(account)
                return balance
            return 0

        elif operation == 'transfer':

            if len(args) == 3:
                t_from = args[0]
                t_to = args[1]
                t_amount = args[2]
                transfer = DoTransfer(t_from, t_to, t_amount)
                return transfer

            else:
                return False

        elif operation == 'transferFrom':
            if len(args) == 3:
                t_from = args[0]
                t_to = args[1]
                t_amount = args[2]
                transfer = DoTransferFrom(t_from,t_to,t_amount)
                return transfer
            return False

        elif operation == 'approve':
            if len(args) == 3:
                t_owner = args[0]
                t_spender = args[1]
                t_amount = args[2]
                approve = DoApprove(t_owner,t_spender,t_amount)
                return approve
            return False

        elif operation == 'allowance':
            if len(args) == 3:
                t_owner = args[0]
                t_spender = args[1]
                approve = GetAllowance(t_owner,t_spender)
                return approve
            return False



        # The following method is not a part of the NEP5 Standard
        # But is used to 'mint' the original tokens
        elif operation == 'deploy':
            result = Deploy()
            return result

        result = 'unknown operation'

        return result


    return False




def DoTransfer(t_from, t_to, amount):

    """
    Method to transfer NEP5 tokens of a specified amount from one account to another

    :param t_from: the address to transfer from
    :type t_from: bytearray

    :param t_to: the address to transfer to
    :type t_to: bytearray

    :param amount: the amount of NEP5 tokens to transfer
    :type amount: int

    :return: whether the transfer was successful
    :rtype: bool

    """
    if amount <= 0:
        return False

    from_is_sender = CheckWitness(t_from)

    if from_is_sender:

        if t_from == t_to:
            return True

        context = GetContext()

        from_val = Get(context, t_from)

        if from_val < amount:
            return False

        if from_val == amount:
            Delete(context, t_from)

        else:
            difference = from_val - amount
            Put(context, t_from, difference)

        to_value = Get(context, t_to)

        to_total = to_value + amount

        Put(context, t_to, to_total)

        OnTransfer(t_from, t_to, amount)

        return True
    else:
        Log("from address is not the tx sender")

    return False



def DoTransferFrom(t_from, t_to, amount):

    """
    Method to transfer NEP5 tokens of a specified amount from one account to another

    :param t_from: the address to transfer from
    :type t_from: bytearray

    :param t_to: the address to transfer to
    :type t_to: bytearray

    :param amount: the amount of NEP5 tokens to transfer
    :type amount: int

    :return: whether the transfer was successful
    :rtype: bool

    """
    if amount <= 0:
        return False

    context = GetContext()

    available_key = concat(t_from, t_to)

    available_to_to_addr = Get(context, available_key)

    if available_to_to_addr < amount:
        Log("Insufficient funds approved")
        return False

    from_balance = Get(context, t_from)

    if from_balance < amount:
        Log("Insufficient tokens in from balance")
        return False

    to_balance = Get(context, t_to)


    new_from_balance = from_balance - amount

    new_to_balance = to_balance + amount

    Put(context, t_to, new_to_balance)
    Put(context, t_from, new_from_balance)

    Log("transfer complete")

    OnTransfer(t_from, t_to, amount)

    return True


def DoApprove(t_owner, t_spender, amount):
    """

    @param t_owner: Owner of tokens
    @param t_spender: Requestor of tokens
    @param amount: Amount requested to be spent by Requestor on behalf of owner
    @return:
    """
    owner_is_sender = CheckWitness(t_owner)

    if not owner_is_sender:
        Log("Incorrect permission")
        return False

    context = GetContext()

    from_balance = Get(context,t_owner)

    # cannot approve an amount that is
    # currently greater than the from balance
    if from_balance >= amount:

        approval_key = concat(t_owner, t_spender)

        current_approved_balance = Get(context, approval_key)

        new_approved_balance = current_approved_balance + amount

        Put(context, approval_key, new_approved_balance)

        Log("Approved")

        OnApprove(t_owner, t_spender, amount)

        return True

    return False


def GetAllowance(t_owner, t_spender):
    """
    @param t_owner: Owner of tokens
    @param t_spender: Requestor of tokens
    @return: int: Amount allowed to be spent by Requestor on behalf of owner

    """

    context = GetContext()

    allowance_key = concat(t_owner, t_spender)

    amount = Get(context, allowance_key)

    return amount

def BalanceOf(account):

    """
    Method to return the current balance of an address

    :param account: the account address to retrieve the balance for
    :type account: bytearray

    :return: the current balance of an address
    :rtype: int

    """
    context = GetContext()

    balance = Get(context, account)

    return balance



def Deploy():
    """
    This is used to distribute the initial tokens to the owner

    @return: bool: whether the deploy was successful

    """
    if not CheckWitness(OWNER):
        Log("Must be owner to deploy")
        return False

    context = GetContext()
    has_deployed = Get(context, 'initialized')

    if has_deployed == 0:

        # do deploy logic
        Put(context, 'initialized', 1)

        Put(context, OWNER, TOTAL_SUPPLY)

        return True

    Log('Could not deploy')
    return False