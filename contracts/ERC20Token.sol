pragma solidity ^0.6.4;

import "./erc20/MintableToken.sol";

contract ERC20Token is MintableToken {
    constructor() public {
        mint(owner, 100 ether);
    }
}
