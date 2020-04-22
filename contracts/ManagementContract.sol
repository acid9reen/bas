pragma solidity ^0.6.4;

import "./ServiceProviderWallet.sol";
import "./BatteryManagement.sol";
import "./lib/Ownable.sol";

contract MgmtContract is Ownable{

    // Wallet contract
    //ServiceProviderWallet public walletContract;

    // Price for creating one battery
    uint256 batFee;

    constructor(address _wallet, uint256 _batFee) public{
        batFee = _batFee;
        //walletContract = ServiceProviderWallet(_wallet);
    } 
}