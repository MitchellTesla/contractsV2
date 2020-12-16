#!/usr/bin/python3

import pytest
from brownie import network, Contract, Wei, chain


@pytest.fixture(scope="module")
def requireMainnetFork():
    assert (network.show_active() == "mainnet-fork"
            or network.show_active() == "mainnet-fork-alchemy")


@pytest.fixture(scope="module")
def setFeesController(bzx, stakingV1, accounts):
    bzx.setFeesController(stakingV1, {"from": bzx.owner()})
    assets = [
        "0x56d811088235F11C8920698a204A5010a788f4b3",  # BZRX
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
        "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",  # AAVE
        "0xdd974D5C2e2928deA5F71b9825b8b646686BD200",  # KNC
        "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",  # MKR
        "0x514910771AF9Ca656af840dff83E8264EcF986CA",  # LINK
        "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",  # YFI
    ]
    bzx.withdrawFees(assets, accounts[8], 0, {'from': stakingV1})


@pytest.fixture(scope="module")
def vBZRX(accounts, BZRXVestingToken):
    vBZRX = loadContractFromAbi(
        "0xb72b31907c1c95f3650b64b2469e08edacee5e8f", "vBZRX", BZRXVestingToken.abi)
    vBZRX.transfer(accounts[0], 1000*10**18, {'from': vBZRX.address})
    return vBZRX


@pytest.fixture(scope="module")
def LPT(accounts):
    LPT = loadContractFromEtherscan(
        "0xe26A220a341EAca116bDa64cF9D5638A935ae629", "LPT")
    return LPT


@pytest.fixture(scope="module")
def iUSDC(accounts, LoanTokenLogicStandard):
    iUSDC = loadContractFromAbi(
        "0x32E4c68B3A4a813b710595AebA7f6B7604Ab9c15", "iUSDC", LoanTokenLogicStandard.abi)
    return iUSDC


@pytest.fixture(scope="module")
def WETH(accounts, TestWeth):
    WETH = loadContractFromAbi(
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "WETH", TestWeth.abi)
    return WETH


@pytest.fixture(scope="module")
def USDC(accounts, TestToken):
    USDC = loadContractFromAbi(
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC", TestToken.abi)
    return USDC


@pytest.fixture(scope="module")
def BZRX(accounts, TestToken):
    BZRX = loadContractFromAbi(
        "0x56d811088235F11C8920698a204A5010a788f4b3", "BZRX", TestToken.abi)
    BZRX.transfer(accounts[0], 1000*10**18, {'from': BZRX.address})
    return BZRX


@pytest.fixture(scope="module")
def iBZRX(accounts, BZRX, LoanTokenLogicStandard):
    iBZRX = loadContractFromAbi(
        "0x18240BD9C07fA6156Ce3F3f61921cC82b2619157", "iBZRX", LoanTokenLogicStandard.abi)
    BZRX.approve(iBZRX, 10*10**50, {'from': accounts[0]})
    iBZRX.mint(accounts[0], 100*10**18, {'from': accounts[0]})
    return iBZRX


def loadContractFromEtherscan(address, alias):
    try:
        return Contract(alias)
    except ValueError:
        contract = Contract.from_explorer(address)
        contract.set_alias(alias)
        return contract


def loadContractFromAbi(address, alias, abi):
    try:
        return Contract(alias)
    except ValueError:
        contract = Contract.from_abi(alias, address=address, abi=abi)
        return contract


def testStake_UserStory1_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, LPT, accounts, iUSDC, USDC, WETH):

    # mint some for testing
    BZRX.transfer(accounts[1], 200e18, {'from': BZRX})
    BZRX.approve(iBZRX, 100e18, {'from': accounts[1]})
    iBZRX.mint(accounts[1], 100e18, {'from': accounts[1]})

    vBZRX.transfer(accounts[1], 100e18, {'from': vBZRX})
    LPT.transferFrom("0x7d9048a13a96657b12dd69bbd8999e1be1c7d97c", accounts[1], 100e18, {
                     'from': "0x7d9048a13a96657b12dd69bbd8999e1be1c7d97c"})

    balanceOfBZRX = BZRX.balanceOf(accounts[1])
    balanceOfvBZRX = vBZRX.balanceOf(accounts[1])
    balanceOfiBZRX = iBZRX.balanceOf(accounts[1])
    balanceOfLPT = LPT.balanceOf(accounts[1])

    BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[1]})
    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[1]})
    iBZRX.approve(stakingV1, balanceOfiBZRX, {'from': accounts[1]})
    # LPT.approve(stakingV1, balanceOfLPT, {'from': accounts[1]})

    tokens = [BZRX, vBZRX, iBZRX]
    amounts = [balanceOfBZRX, balanceOfvBZRX, balanceOfiBZRX]
    tx = stakingV1.stake(tokens, amounts, accounts[1], {'from': accounts[1]})

    balances = stakingV1.balanceOfByAssetTotal({'from': accounts[1]})
    assert(balances[0] == 100e18)
    assert(balances[1] == 100e18)
    assert(balances[2] == 100e18)
    assert(balances[3] == 0)
    
    assert True


def testStake_UserStory2_StakedMoreTokens(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):


    # mint some for testing
    BZRX.transfer(accounts[1], 200e18, {'from': BZRX})
    BZRX.approve(iBZRX, 100e18, {'from': accounts[1]})
    iBZRX.mint(accounts[1], 100e18, {'from': accounts[1]})

    vBZRX.transfer(accounts[1], 100e18, {'from': vBZRX})
    # LPT.transferFrom("0x7d9048a13a96657b12dd69bbd8999e1be1c7d97c", accounts[1], 100e18, {
    #                  'from': "0x7d9048a13a96657b12dd69bbd8999e1be1c7d97c"})

    balanceOfBZRX = BZRX.balanceOf(accounts[1])
    balanceOfvBZRX = vBZRX.balanceOf(accounts[1])
    balanceOfiBZRX = iBZRX.balanceOf(accounts[1])
    # balanceOfLPT = LPT.balanceOf(accounts[1])

    BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[1]})
    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[1]})
    iBZRX.approve(stakingV1, balanceOfiBZRX, {'from': accounts[1]})
    # LPT.approve(stakingV1, balanceOfLPT, {'from': accounts[1]})

    tokens = [BZRX, vBZRX, iBZRX]
    amounts = [balanceOfBZRX, balanceOfvBZRX, balanceOfiBZRX]
    tx = stakingV1.stake(tokens, amounts, accounts[1], {'from': accounts[1]})

    balances = stakingV1.balanceOfByAssetTotal({'from': accounts[1]})
    assert(balances[0] == 100e18)
    assert(balances[1] == 100e18)
    assert(balances[2] == 100e18)
    assert(balances[3] == 0)


        # mint some for testing
    BZRX.transfer(accounts[1], 200e18, {'from': BZRX})
    BZRX.approve(iBZRX, 100e18, {'from': accounts[1]})
    iBZRX.mint(accounts[1], 100e18, {'from': accounts[1]})

    vBZRX.transfer(accounts[1], 100e18, {'from': vBZRX})
    # LPT.transferFrom("0x7d9048a13a96657b12dd69bbd8999e1be1c7d97c", accounts[1], 100e18, {
    #                  'from': "0x7d9048a13a96657b12dd69bbd8999e1be1c7d97c"})

    balanceOfBZRX = BZRX.balanceOf(accounts[1])
    balanceOfvBZRX = vBZRX.balanceOf(accounts[1])
    balanceOfiBZRX = iBZRX.balanceOf(accounts[1])
    # balanceOfLPT = LPT.balanceOf(accounts[1])

    BZRX.approve(stakingV1, balanceOfBZRX, {'from': accounts[1]})
    vBZRX.approve(stakingV1, balanceOfvBZRX, {'from': accounts[1]})
    iBZRX.approve(stakingV1, balanceOfiBZRX, {'from': accounts[1]})
    # LPT.approve(stakingV1, balanceOfLPT, {'from': accounts[1]})

    tokens = [BZRX, vBZRX, iBZRX]
    amounts = [balanceOfBZRX, balanceOfvBZRX, balanceOfiBZRX]
    tx = stakingV1.stake(tokens, amounts, accounts[1], {'from': accounts[1]})

    balances = stakingV1.balanceOfByAssetTotal({'from': accounts[1]})
    assert(balances[0] == 200e18)
    assert(balances[1] == 200e18)
    assert(balances[2] == 200e18)
    assert(balances[3] == 0)


    assert True


def testStake_UserStory3_IClaimMyIncentiveRewards(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):
    # TODO @Tom
    assert False


def testStake_UserStory4_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory5_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory6_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory7_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory8_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory9_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory10_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False


def testStake_UserStory11_StakedFirstTime(requireMainnetFork, stakingV1, bzx, setFeesController, BZRX, vBZRX, iBZRX, accounts, iUSDC, USDC, WETH):

    assert False