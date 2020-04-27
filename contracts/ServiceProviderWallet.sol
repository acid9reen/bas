pragma solidity 0.6.4;

import './lib/Ownable.sol';

contract ServiceProviderWallet is Ownable {
    // To notify the receipt of new funds
    // - address from which funds are transferred
    // - amount of receipt
    event Received(address, uint256);

    // For notification of the issuance of part of the funds
    // - address, which initiated the issuance of funds
    // - address to which funds are directed
    // - amount to issue
    event Withdraw(address, address, uint256);

    receive() external payable {
        require(msg.value > 0, "Negative value!");
        emit Received(msg.sender, msg.value);
    }

    // Used to issue part of the funds from the address of the contract
    function withdraw(address payable _to, uint256 _value) external onlyOwner{
        _to.transfer(_value);
        emit Withdraw(msg.sender, _to, _value);
    }

    // Allows to delete a contract
    function kill() external onlyOwner{
        require(msg.sender == owner);
        selfdestruct(msg.sender);
    }
}
