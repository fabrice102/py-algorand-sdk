from behave import given, when, then, register_type
import base64
from algosdk import kmd
from algosdk.future import transaction
from algosdk import encoding
from algosdk.v2client import *
from algosdk import account
from algosdk import mnemonic
from algosdk import wallet
from algosdk import auction
from algosdk import util
from algosdk import constants
from algosdk.future import template
import os
from datetime import datetime
import hashlib
import json
import random
import time
import urllib
from urllib.request import Request, urlopen
import parse

@parse.with_pattern(r".*")
def parse_string(text):
    return text

register_type(MaybeString=parse_string)

@given("mock server recording request paths")
def setup_mockserver(context):
    context.url = "http://127.0.0.1:" + str(context.path_server_port)
    context.acl = algod.AlgodClient("algod_token", context.url)
    context.icl = indexer.IndexerClient("indexer_token", context.url)

@given('mock http responses in "{jsonfiles}" loaded from "{directory}"')
def mock_response(context, jsonfiles, directory):
    context.url = "http://127.0.0.1:" + str(context.response_server_port)
    context.acl = algod.AlgodClient("algod_token", context.url)
    context.icl = indexer.IndexerClient("indexer_token", context.url)

    # The mock server writes this response to a file, on a regular request
    # that file is read.
    # It's an interesting approach, but currently doesn't support setting
    # the content type, or different return codes. This will require a bit
    # of extra work when/if we support the different error cases.
    #
    # Take a look at 'environment.py' to see the mock servers.
    req = Request(context.url+"/mock/"+directory + "/" +jsonfiles, method="GET")
    urlopen(req)

@when('we make a Pending Transaction Information against txid "{txid}" with format "{response_format}"')
def pending_txn_info(context, txid, response_format):
    context.response = context.acl.pending_transaction_info(txid, response_format=response_format)

@when('we make a Pending Transaction Information with max {max} and format "{response_format}"')
def pending_txn_with_max(context, max, response_format):
    context.response = context.acl.pending_transactions(int(max), response_format=response_format)

@when('we make any Pending Transactions Information call')
def pending_txn_any(context):
    context.response = context.acl.pending_transactions(100, response_format="msgpack")

@when('we make any Pending Transaction Information call')
def pending_txn_any2(context):
    context.response = context.acl.pending_transaction_info("sdfsf", response_format="msgpack")

@then('the parsed Pending Transaction Information response should have sender "{sender}"')
def parse_pending_txn(context, sender):
    context.response = json.loads(context.response)
    assert encoding.encode_address(base64.b64decode(context.response["txn"]["txn"]["snd"])) == sender

@then('the parsed Pending Transactions Information response should contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_pending_txns(context, length, idx, sender):
    context.response = json.loads(context.response)
    assert len(context.response["top-transactions"]) == int(length)
    assert encoding.encode_address(base64.b64decode(context.response["top-transactions"][int(idx)]["txn"]["snd"])) == sender

@when('we make a Pending Transactions By Address call against account "{account}" and max {max} and format "{response_format}"')
def pending_txns_by_addr(context, account, max, response_format):
    context.response = context.acl.pending_transactions_by_address(account, limit=int(max), response_format=response_format)

@when('we make any Pending Transactions By Address call')
def pending_txns_by_addr_any(context):
    context.response = context.acl.pending_transactions_by_address("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI", response_format="msgpack")

@then('the parsed Pending Transactions By Address response should contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_pend_by_addr(context, length, idx, sender):
    context.response = json.loads(context.response)
    assert len(context.response["top-transactions"]) == int(length)
    assert encoding.encode_address(base64.b64decode(context.response["top-transactions"][int(idx)]["txn"]["snd"])) == sender

@when('we make any Send Raw Transaction call')
def send_any(context):
    context.response = context.acl.send_raw_transaction("Bg==")

@then('the parsed Send Raw Transaction response should have txid "{txid}"')
def parsed_send(context, txid):
    assert context.response == txid

@when('we make any Node Status call')
def status_any(context):
    context.response = context.acl.status()

@then('the parsed Node Status response should have a last round of {roundNum}')
def parse_status(context, roundNum):
    assert context.response["last-round"] == int(roundNum)

@when('we make a Status after Block call with round {block}')
def status_after(context, block):
    context.response = context.acl.status_after_block(int(block))

@when('we make any Status After Block call')
def status_after_any(context):
    context.response = context.acl.status_after_block(3)

@then('the parsed Status After Block response should have a last round of {roundNum}')
def parse_status_after(context, roundNum):
    assert context.response["last-round"] == int(roundNum)

@when('we make any Ledger Supply call')
def ledger_any(context):
    context.response = context.acl.ledger_supply()

@then('the parsed Ledger Supply response should have totalMoney {tot} onlineMoney {online} on round {roundNum}')
def parse_ledger(context, tot, online, roundNum):
    assert context.response["online-money"] == int(online)
    assert context.response["total-money"] == int(tot)
    assert context.response["current_round"] == int(roundNum)

@when('we make an Account Information call against account "{account}"')
def acc_info(context, account):
    context.response = context.acl.account_info(account)

@when('we make any Account Information call')
def acc_info_any(context):
    context.response = context.acl.account_info("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI")

@then('the parsed Account Information response should have address "{address}"')
def parse_acc_info(context, address):
    assert context.response["address"] == address

@when('we make a Get Block call against block number {block} with format "{response_format}"')
def block(context, block, response_format):
    context.response = context.acl.block_info(int(block), response_format=response_format)

@when('we make any Get Block call')
def block_any(context):
    context.response = context.acl.block_info(3, response_format="msgpack")

@then('the parsed Get Block response should have rewards pool "{pool}"')
def parse_block(context, pool):
    context.response = json.loads(context.response)
    assert context.response["block"]["rwd"] == pool

@when('I get the next page using {indexer} to lookup asset balances for {assetid} with {currencygt}, {currencylt}, {limit}')
def next_asset_balance(context, indexer, assetid, currencygt, currencylt, limit):
    context.response = context.icls[indexer].asset_balances(int(assetid), min_balance=int(currencygt), max_balance=int(currencylt), limit=int(limit), next_page=context.response["next-token"])

@then('There are {numaccounts} with the asset, the first is "{account}" has "{isfrozen}" and {amount}')
def check_asset_balance(context, numaccounts, account, isfrozen, amount):
    assert len(context.response["balances"]) == int(numaccounts)
    assert context.response["balances"][0]["address"] == account
    assert context.response["balances"][0]["amount"] == int(amount)
    assert context.response["balances"][0]["is-frozen"] == (isfrozen == "true")

@when('we make a Lookup Asset Balances call against asset index {index} with limit {limit} afterAddress "{afterAddress:MaybeString}" round {block} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan}')
def asset_balance(context, index, limit, afterAddress, block, currencyGreaterThan, currencyLessThan):
    context.response = context.icl.asset_balances(int(index), int(limit), next_page=None, min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan), block=int(block))

@when('we make any LookupAssetBalances call')
def asset_balance_any(context):
    context.response = context.icl.asset_balances(123, 10)

@then('the parsed LookupAssetBalances response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have address "{address}" amount {amount} and frozen state "{frozenState}"')
def parse_asset_balance(context, roundNum, length, idx, address, amount, frozenState):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["balances"]) == int(length)
    assert context.response["balances"][int(idx)]["address"] == address
    assert context.response["balances"][int(idx)]["amount"] == int(amount)
    assert context.response["balances"][int(idx)]["is-frozen"] == (frozenState == "true")

@when('I use {indexer} to search for all {assetid} asset transactions')
def icl_asset_txns(context, indexer, assetid):
    context.response = context.icls[indexer].search_asset_transactions(int(assetid))

@when('we make a Lookup Asset Transactions call against asset index {index} with NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} address "{address:MaybeString}" addressRole "{addressRole:MaybeString}" ExcluseCloseTo "{excludeCloseTo:MaybeString}"')
def asset_txns(context, index, notePrefixB64, txType, sigType, txid, block, minRound, maxRound, limit, beforeTime, afterTime, currencyGreaterThan, currencyLessThan, address, addressRole, excludeCloseTo):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if address == "none":
        address = None
    if addressRole == "none":
        addressRole = None
    if excludeCloseTo == "none":
        excludeCloseTo = None
    context.response = context.icl.search_asset_transactions(int(index), limit=int(limit), next_page=None, note_prefix=base64.b64decode(notePrefixB64), txn_type=txType,
        sig_type=sigType, txid=txid, block=int(block), min_round=int(minRound), max_round=int(maxRound),
        start_time=afterTime, end_time=beforeTime, min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan), address=address, address_role=addressRole,
        exclude_close_to=excludeCloseTo)

@when('we make any LookupAssetTransactions call')
def asset_txns_any(context):
    context.response = context.icl.search_asset_transactions(32)

@then('the parsed LookupAssetTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_asset_tns(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    assert context.response["transactions"][int(idx)]["sender"] == sender
    
@when('I use {indexer} to search for all "{accountid}" transactions')
def icl_txns_by_addr(context, indexer, accountid):
    context.response = context.icls[indexer].search_transactions_by_address(accountid)

@when('we make a Lookup Account Transactions call against account "{account:MaybeString}" with NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index}')
def txns_by_addr(context, account, notePrefixB64, txType, sigType, txid, block, minRound, maxRound, limit, beforeTime, afterTime, currencyGreaterThan, currencyLessThan, index):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    context.response = context.icl.search_transactions_by_address(asset_id=int(index), limit=int(limit), next_page=None, note_prefix=base64.b64decode(notePrefixB64), txn_type=txType,
        sig_type=sigType, txid=txid, block=int(block), min_round=int(minRound), max_round=int(maxRound),
        start_time=afterTime, end_time=beforeTime, min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan), address=account)

@when('we make any LookupAccountTransactions call')
def txns_by_addr_any(context):
    context.response = context.icl.search_transactions_by_address("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI")

@then('the parsed LookupAccountTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_txns_by_addr(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(idx)]["sender"] == sender

@when('I use {indexer} to lookup block {number}')
def icl_lookup_block(context, indexer, number):
    context.response = context.icls[indexer].block_info(int(number))

@then('The block was confirmed at {timestamp}, contains {num} transactions, has the previous block hash "{prevHash}"')
def icl_block_check(context, timestamp, num, prevHash):
    assert context.response["previous-block-hash"] == prevHash
    assert len(context.response["transactions"]) == int(num)
    assert context.response["timestamp"] == int(timestamp)

@when('we make a Lookup Block call against round {block}')
def lookup_block(context, block):
    context.response = context.icl.block_info(int(block))

@when('we make any LookupBlock call')
def lookup_block_any(context):
    context.response = context.icl.block_info(12)

@then('the parsed LookupBlock response should have previous block hash "{prevHash}"')
def parse_lookup_block(context, prevHash):
    assert context.response["previous-block-hash"] == prevHash

@then('The account has {num} assets, the first is asset {index} has a frozen status of "{frozen}" and amount {units}.')
def lookup_account_check(context, num, index, frozen, units):
    assert len(context.response["account"]["assets"]) == int(num)
    assert context.response["account"]["assets"][0]["asset-id"] == int(index)
    assert context.response["account"]["assets"][0]["is-frozen"] == (frozen == "true")
    assert context.response["account"]["assets"][0]["amount"] == int(units)

@then('The account created {num} assets, the first is asset {index} is named "{name}" with a total amount of {total} "{unit}"')
def lookup_account_check_created(context, num, index, name, total, unit):
    assert len(context.response["account"]["created-assets"]) == int(num)
    assert context.response["account"]["created-assets"][0]["index"] == int(index)
    assert context.response["account"]["created-assets"][0]["params"]["name"] == name
    assert context.response["account"]["created-assets"][0]["params"]["unit-name"] == unit
    assert context.response["account"]["created-assets"][0]["params"]["total"] == int(total)

@then('The account has {μalgos} μalgos and {num} assets, {assetid} has {assetamount}')
def lookup_account_check_holdings(context, μalgos, num, assetid, assetamount):
    assert context.response["account"]["amount"] == int(μalgos)
    assert len(context.response["account"].get("assets", [])) == int(num)
    if int(num) > 0:
        assets = context.response["account"]["assets"]
        for a in assets:
            if a["asset-id"] == int(assetid):
                assert a["amount"] == int(assetamount)

@when('I use {indexer} to lookup account "{account}" at round {round}')
def icl_lookup_account_at_round(context, indexer, account, round):
    context.response = context.icls[indexer].account_info(account, int(round))

@when('we make a Lookup Account by ID call against account "{account}" with round {block}')
def lookup_account(context, account, block):
    context.response = context.icl.account_info(account, int(block))

@when("we make any LookupAccountByID call")
def lookup_account_any(context):
    context.response = context.icl.account_info("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI", 12)

@then('the parsed LookupAccountByID response should have address "{address}"')
def parse_account(context, address):
    assert context.response["account"]["address"] == address

@when('I use {indexer} to lookup asset balances for {assetid} with {currencygt}, {currencylt}, {limit} and token "{token}"')
def icl_asset_balance(context, indexer, assetid, currencygt, currencylt, limit, token):
    context.response = context.icls[indexer].asset_balances(int(assetid), min_balance=int(currencygt), max_balance=int(currencylt), limit=int(limit), next_page=token)

def parse_args(assetid):
    t = assetid.split(" ")
    l = {
        "assetid": t[2],
        "currencygt": t[4][:-1],
        "currencylt": t[5][:-1],
        "limit": t[6],
        "token": t[9][1:-1]
        }
    return l

@when('I use {indexer} to lookup asset {assetid}')
def icl_lookup_asset(context, indexer, assetid):
    try:
        context.response = context.icls[indexer].asset_info(int(assetid))
    except:
        icl_asset_balance(context, indexer, **parse_args(assetid))

@then('The asset found has: "{name}", "{units}", "{creator}", {decimals}, "{defaultfrozen}", {total}, "{clawback}"')
def check_lookup_asset(context, name, units, creator, decimals, defaultfrozen, total, clawback):
    assert context.response["asset"]["params"]["name"] == name
    assert context.response["asset"]["params"]["unit-name"] == units
    assert context.response["asset"]["params"]["creator"] == creator
    assert context.response["asset"]["params"]["decimals"] == int(decimals)
    assert context.response["asset"]["params"]["default-frozen"] == (defaultfrozen == "true")
    assert context.response["asset"]["params"]["total"] == int(total)
    assert context.response["asset"]["params"]["clawback"] == clawback

@when('we make a Lookup Asset by ID call against asset index {index}')
def lookup_asset(context, index):
    context.response = context.icl.asset_info(int(index))

@when('we make any LookupAssetByID call')
def lookup_asset_any(context):
    context.response = context.icl.asset_info(1)

@then('the parsed LookupAssetByID response should have index {index}')
def parse_asset(context, index):
    assert context.response["asset"]["index"] == int(index)

@when('we make a Search Accounts call with assetID {index} limit {limit} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} and round {block}')
def search_accounts(context, index, limit, currencyGreaterThan, currencyLessThan, block):
    context.response = context.icl.accounts(asset_id=int(index), limit=int(limit), next_page=None, min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan), block=int(block))

@when('I use {indexer} to search for an account with {assetid}, {limit}, {currencygt}, {currencylt} and token "{token:MaybeString}"')
def icl_search_accounts(context, indexer, assetid, limit, currencygt, currencylt, token):
    context.response = context.icls[indexer].accounts(asset_id=int(assetid), limit=int(limit), next_page=token, min_balance=int(currencygt),
        max_balance=int(currencylt))

@then('I get the next page using {indexer} to search for an account with {assetid}, {limit}, {currencygt} and {currencylt}')
def search_accounts_nex(context, indexer, assetid, limit, currencygt, currencylt):
    context.response = context.icls[indexer].accounts(asset_id=int(assetid), limit=int(limit), min_balance=int(currencygt),
        max_balance=int(currencylt), next_page=context.response["next-token"])

@then('There are {num}, the first has {pendingrewards}, {rewardsbase}, {rewards}, {withoutrewards}, "{address}", {amount}, "{status}", "{sigtype:MaybeString}"')
def check_search_accounts(context, num, pendingrewards, rewardsbase, rewards, withoutrewards, address, amount, status, sigtype):
    assert len(context.response["accounts"]) == int(num)
    assert context.response["accounts"][0]["pending-rewards"] == int(pendingrewards)
    assert context.response["accounts"][0].get("rewards-base", 0) == int(rewardsbase)
    assert context.response["accounts"][0]["rewards"] == int(rewards)
    assert context.response["accounts"][0]["amount-without-pending-rewards"] == int(withoutrewards)
    assert context.response["accounts"][0]["address"] == address
    assert context.response["accounts"][0]["amount"] == int(amount)
    assert context.response["accounts"][0]["status"] == status
    assert context.response["accounts"][0].get("sig-type", "") == sigtype

@then('The first account is online and has "{address}", {keydilution}, {firstvalid}, {lastvalid}, "{votekey}", "{selectionkey}"')
def check_search_accounts_online(context, address, keydilution, firstvalid, lastvalid, votekey, selectionkey):
    assert context.response["accounts"][0]["status"] == "Online"
    assert context.response["accounts"][0]["address"] == address
    assert context.response["accounts"][0]["participation"]["vote-key-dilution"] == int(keydilution)
    assert context.response["accounts"][0]["participation"]["vote-first-valid"] == int(firstvalid)
    assert context.response["accounts"][0]["participation"]["vote-last-valid"] == int(lastvalid)
    assert context.response["accounts"][0]["participation"]["vote-participation-key"] == votekey
    assert context.response["accounts"][0]["participation"]["selection-participation-key"] == selectionkey

@when('we make any SearchAccounts call')
def search_accounts_any(context):
    context.response = context.icl.accounts(asset_id=2)

@then('the parsed SearchAccounts response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have address "{address}"')
def parse_accounts(context, roundNum, length, index, address):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["accounts"]) == int(length)
    if int(length) > 0:
        assert context.response["accounts"][int(index)]["address"] == address

@when('I get the next page using {indexer} to search for transactions with {limit} and {maxround}')
def search_txns_next(context, indexer, limit, maxround):
    context.response = context.icls[indexer].search_transactions(limit=int(limit), max_round=int(maxround), next_page=context.response["next-token"])

@when('I use {indexer} to search for transactions with {limit}, "{noteprefix:MaybeString}", "{txtype:MaybeString}", "{sigtype:MaybeString}", "{txid:MaybeString}", {block}, {minround}, {maxround}, {assetid}, "{beforetime:MaybeString}", "{aftertime:MaybeString}", {currencygt}, {currencylt}, "{address:MaybeString}", "{addressrole:MaybeString}", "{excludecloseto:MaybeString}" and token "{token:MaybeString}"')
def icl_search_txns(context, indexer, limit, noteprefix, txtype, sigtype, txid, block, minround, maxround, assetid, beforetime, aftertime, currencygt, currencylt, address, addressrole, excludecloseto, token):
    context.response = context.icls[indexer].search_transactions(asset_id=int(assetid), limit=int(limit), next_page=token, 
        note_prefix=base64.b64decode(noteprefix), txn_type=txtype,
        sig_type=sigtype, txid=txid, block=int(block), min_round=int(minround), max_round=int(maxround),
        start_time=aftertime, end_time=beforetime, min_amount=int(currencygt),
        max_amount=int(currencylt), address=address, address_role=addressrole,
        exclude_close_to=excludecloseto=="true")

@then('there are {num} transactions in the response, the first is "{txid:MaybeString}".')
def check_transactions(context, num, txid):
    assert len(context.response["transactions"]) == int(num)
    if int(num) > 0:
        assert context.response["transactions"][0]["id"] == txid

@then('Every transaction has tx-type "{txtype}"')
def check_transaction_types(context, txtype):
    for txn in context.response["transactions"]:
        assert txn["tx-type"] == txtype

@then('Every transaction has sig-type "{sigtype}"')
def check_sig_types(context, sigtype):
    for txn in context.response["transactions"]:
        if sigtype == "lsig":
            assert list(txn["signature"].keys())[0] == "logicsig"
        if sigtype == "msig":
            assert list(txn["signature"].keys())[0] == "multisig"
        if sigtype == "sig":
            assert list(txn["signature"].keys())[0] == sigtype

@then('Every transaction has round >= {minround}')
def check_minround(context, minround):
    for txn in context.response["transactions"]:
        assert txn["confirmed-round"] >= int(minround)

@then('Every transaction has round <= {maxround}')
def check_maxround(context, maxround):
    for txn in context.response["transactions"]:
        assert txn["confirmed-round"] <= int(maxround)

@then('Every transaction has round {block}')
def check_round(context, block):
    for txn in context.response["transactions"]:
        assert txn["confirmed-round"] == int(block)

@then('Every transaction works with asset-id {assetid}')
def check_assetid(context, assetid):
    for txn in context.response["transactions"]:
        if "asset-config-transaction" in txn:
            subtxn = txn["asset-config-transaction"]
        else:
            subtxn = txn["asset-transfer-transaction"]
        assert subtxn["asset-id"] == int(assetid) or txn["created-asset-index"] == int(assetid)

@then('Every transaction is older than "{before}"')
def check_before(context, before):
    for txn in context.response["transactions"]:
        t = datetime.fromisoformat(before.replace("Z", "+00:00"))
        assert txn["round-time"] <= datetime.timestamp(t)

@then('Every transaction is newer than "{after}"')
def check_after(context, after):
    t = True
    for txn in context.response["transactions"]:
        t = datetime.fromisoformat(after.replace("Z", "+00:00"))
        if not txn["round-time"] >= datetime.timestamp(t):
            t = False
    assert t


@then('Every transaction moves between {currencygt} and {currencylt} currency')
def check_currency(context, currencygt, currencylt):
    for txn in context.response["transactions"]:
        amt = 0
        if "asset-transfer-transaction" in txn:
            amt = txn["asset-transfer-transaction"]["amount"]
        else:
            amt = txn["payment-transaction"]["amount"]
        if int(currencygt) == 0:
            if int(currencylt) > 0:
                assert amt <= int(currencylt)
        else:
            if int(currencylt) > 0:
                assert int(currencygt) <= amt <= int(currencylt)
            else:
                assert int(currencygt) <= amt
                
        
@when('we make a Search For Transactions call with account "{account:MaybeString}" NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index} addressRole "{addressRole:MaybeString}" ExcluseCloseTo "{excludeCloseTo:MaybeString}"')
def search_txns(context, account, notePrefixB64, txType, sigType, txid, block, minRound, maxRound, limit, beforeTime, afterTime, currencyGreaterThan, currencyLessThan, index, addressRole, excludeCloseTo):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if account == "none":
        account = None
    if addressRole == "none":
        addressRole = None
    if excludeCloseTo == "none":
        excludeCloseTo = None
    context.response = context.icl.search_transactions(asset_id=int(index), limit=int(limit), next_page=None, note_prefix=base64.b64decode(notePrefixB64), txn_type=txType,
        sig_type=sigType, txid=txid, block=int(block), min_round=int(minRound), max_round=int(maxRound),
        start_time=afterTime, end_time=beforeTime, min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan), address=account, address_role=addressRole,
        exclude_close_to=excludeCloseTo)

@when('we make any SearchForTransactions call')
def search_txns_any(context):
    context.response = context.icl.search_transactions(asset_id=2)

@then('the parsed SearchForTransactions response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have sender "{sender}"')
def parse_search_txns(context, roundNum, length, index, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(index)]["sender"] == sender

@when('I use {indexer} to search for assets with {limit}, {assetidin}, "{creator:MaybeString}", "{name:MaybeString}", "{unit:MaybeString}", and token "{token:MaybeString}"')
def icl_search_assets(context, indexer, limit, assetidin, creator, name, unit, token):
    context.response = context.icls[indexer].search_assets(
        limit=int(limit), next_page=token, creator=creator, name=name, unit=unit,
        asset_id=int(assetidin))

@then('there are {num} assets in the response, the first is {assetidout}.')
def check_assets(context, num, assetidout):
    assert len(context.response["assets"]) == int(num)
    if int(num) > 0:
        assert context.response["assets"][0]["index"] == int(assetidout)

@when('we make a SearchForAssets call with limit {limit} creator "{creator:MaybeString}" name "{name:MaybeString}" unit "{unit:MaybeString}" index {index}')
def search_assets(context, limit, creator, name, unit, index):
    if creator == "none":
        creator = None
    if name == "none":
        name = None
    if unit == "none":
        unit = None
    
    context.response = context.icl.search_assets(limit=int(limit), 
        next_page=None, creator=creator, name=name, unit=unit,
        asset_id=int(index))

@when('we make any SearchForAssets call')
def search_assets_any(context):
    context.response = context.icl.search_assets(asset_id=2)

@then('the parsed SearchForAssets response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have asset index {assetIndex}')
def parse_search_assets(context, roundNum, length, index, assetIndex):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["assets"]) == int(length)
    if int(length) > 0:
        assert context.response["assets"][int(index)]["index"] == int(assetIndex)

@when('we make any Suggested Transaction Parameters call')
def suggested_any(context):
    context.response = context.acl.suggested_params()

@then('the parsed Suggested Transaction Parameters response should have first round valid of {roundNum}')
def parse_suggested(context, roundNum):
    assert context.response.first == int(roundNum)

@then('expect the path used to be "{path}"')
def expect_path(context, path):
    if isinstance(context.response, str):
        context.response = json.loads(context.response)
    exp_path, exp_query = urllib.parse.splitquery(path)
    exp_query = urllib.parse.parse_qs(exp_query)

    actual_path, actual_query = urllib.parse.splitquery(context.response["path"])
    actual_query = urllib.parse.parse_qs(actual_query)
    assert exp_path == actual_path.replace("%3A", ":")
    assert exp_query == actual_query

@then('expect error string to contain "{err:MaybeString}"')
def expect_error(context, err):
    pass

@given('indexer client {index} at "{address}" port {port} with token "{token}"')
def indexer_client(context, index, address, port, token):
    context.icls = {index: indexer.IndexerClient(token, "http://" + address + ":" + str(port))}
    
    
