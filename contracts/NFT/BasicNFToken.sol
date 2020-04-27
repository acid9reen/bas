pragma solidity ^0.6.4;

contract BasicNFToken {
    /// @dev A mapping from Token IDs to the address that owns them.
    ///      Even new token is created with a non-zero owner.
    mapping (bytes20 => address) public tokenIdToOwner;

    /// @dev A mapping from Token IDs to an address that has been approved to call
    ///      transferFrom(). Each Token can only have one approved address for transfer
    ///      at any time. A zero value means no approval is outstanding.
    mapping (bytes20 => address) public tokenIdToApproved;

    // @dev A mapping from Token IDs to vendor address
    mapping (bytes20 => address) public tokenID;

    function _setTokenWithID(bytes20 _tokenId, address _data) internal {
        tokenID[_tokenId] = _data;
    }

    /// @dev Assigns ownership of a specific token to an address.
    function _transfer(address _from, address _to, bytes20 _tokenId) internal {
        // transfer ownership
        tokenIdToOwner[_tokenId] = _to;
        // When creating new token _from is 0x0, but we can't account that address.
        if (_from != address(0)) {
            // clear any previously approved ownership exchange
            delete tokenIdToApproved[_tokenId];
        }
    }
}