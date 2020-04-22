pragma solidity ^0.6.4;

contract ERC20Token {
    address owner;
    constructor()public{
        owner=msg.sender;
    }
    
}
