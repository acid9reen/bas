pragma solidity ^0.6.4;

import "./NFT/BasicNFToken.sol";
import "./ManagementContract.sol";
import "./ERC20Token.sol";
import "./lib/Ownable.sol";

contract BatteryManagement is BasicNFToken, Ownable {
    // To notify the transfer of battery ownership to a new owner
    // - address of the previous owner
    // - address of the new owner
    // - battery identifier
    event Transfer(address indexed, address indexed, bytes20);
    
    ManagementContract public managementContract;
    ERC20Token public erc20;

    // Contract constructor
    // - The address of the contract managing the list of vendors.
    // - address of the contract that manages the tokens in which
    //   the payment for replacing the batteries will occur.
    constructor(address _mgmt, address _erc20) public {
        managementContract = ManagementContract(_mgmt);
        erc20 = ERC20Token(_erc20);
    }
    
    // Creates a new battery
    // The owner of the battery is its current creator.
    // Creating a new battery may only be available.
    // management contract
    // - battery manufacturer address
    // - battery identifier
    function createBattery(address _vendor, bytes20 _tokenId) public {
        require(msg.sender == address(managementContract));
        require(!batteryExists(_tokenId));
        _setTokenWithID(_tokenId, _vendor);
        _transfer(0, _vendor, _tokenId);
    }
    
    // Returns the address of the battery manufacturer
    // - battery identifier
    function vendorOf(bytes20 _batteryId) view public returns(address) {
        return tokenID[_batteryId];
    }
    
    // Checks if a token with this identifier is registered by any of the manufacturers.
    function batteryExists(bytes20 _batteryId) internal view returns (bool) {
        return tokenID[_batteryId] != address(0);
    }
}
