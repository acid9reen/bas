pragma solidity ^0.6.4;

import "./ManagementContract.sol";
import "./ERC20Token.sol";
import "./lib/Ownable.sol";
import "./NFT/BasicNFToken.sol";

contract BatteryManagement is Ownable, BasicNFToken{
    ManagementContract public managementContract;
    ERC20Token public erc20Token;

    //Checking if car has battery
    mapping (address => bool) carHasBattery;

    // Для проверки на повторное использование транзакции
    mapping (bytes32 => bool) reused;


    // To notify the transfer of battery ownership to a new ownerдельцу
    // from - address of the previous owner
    // to - address of the new owner
    // batteryId - battery identifier
    event Transfer(address from, address to, bytes20 batteryId);

    // Contract constructor
    // - The address of the contract managing the list of vendors.
    // - address of the contract that manages the tokens in which it will be
    //    Settlement for battery replacement.
    constructor(address _mgmt, address _erc20Token) public {
        managementContract = ManagementContract(_mgmt);
        erc20Token = ERC20Token(_erc20Token);
    }

    // Creates a new battery
    // The owner of the battery is its current creator.
    // Creating a new battery may only be available.
    // management contract
    // - battery manufacturer address
    // - battery identifier
    function createBattery(address _vendor, bytes20 _tokenId) public {
        require(msg.sender == address(managementContract), "Not enough rights to call");
        require(!batteryExists(_tokenId), "Battery id is not unique");

        _setTokenWithID(_tokenId, _vendor);
        _transfer(address(0), _vendor, _tokenId);
    }

    // Checks if a token with this identifier is registered by any of the manufacturers.
    function batteryExists(bytes20 _batteryId) internal view returns (bool) {
        return tokenID[_batteryId] != address(0);
    }

    // Changes the owner of the battery. Can only be called by
    // current owner
    //_to - address of the new owner
    //_tokenId - battery identifier
    function transfer(address _to, bytes20 _tokenId) public{
        require(msg.sender == tokenIdToOwner[_tokenId], "You do not have enough permissions");
        require(carHasBattery[_to] != true, "Car already has a battery");

        _transfer(msg.sender, _to, _tokenId);
        carHasBattery[_to] = true;

        emit Transfer(msg.sender, _to, _tokenId);
    }

    // Calculates battery Id from information from its firmware
    // _v - v signature component for battery
    // _r - r signature component for the battery
    // _s - s signature component for battery
    // _charges - number of charges
    // _time - time for receiving information
    function getBatteryIdFromSignature(uint8 _v, bytes32 _r, bytes32 _s, uint256 _charges, uint256 _time)
    public pure returns (address batteryId){
    uint256 message = 2**32 * _charges + _time;
    bytes32 h = keccak256(abi.encode(message));
    batteryId = ecrecover(h, _v, _r, _s);
    }

    // Возвращает адрес производителя батареи
    // - идентификатор батареи
    function vendorOf(bytes20 _batteryId) public view returns(address){
        return tokenID[_batteryId];
    }


    // Высчитывает хэш, используемый для проверки на повторное
    // использование транзакции
    // - адрес, полученный из подписи и хэша транзакции
    // - количество заряда батареи
    // - время получения информации о батарее
    function generateStatusUsageHash(address _addr, uint256 _charges, uint256 _time)
    internal pure returns (bytes32){
        return keccak256(abi.encodePacked(_addr, _charges, _time));
    }


    // Проверяет цифровую подпись для данных и возвращает результат
    // проверки и адрес вендора.
    // Результат проверки: 0 - результат проверки цифровой подписи, показывает
    // что она сделана батареей, для которой существует токен; 1 - транзакция
    // с таким статусом уже отправлялась в блокчейн, что указывает на возможную
    // прослушку траффика; 2 - для батареи нет соответствующего токена; 999 -
    // другая ошибка.
    // - число зарядов
    // - временная метка
    // - v, r, s компоненты цифровой подписи
    function verifyBattery(uint8 _v, bytes32 _r, bytes32 _s, uint256 _charges, uint256 _time) public view
    returns(bool, address) {
        address batteryId = getBatteryIdFromSignature(_v, _r, _s, _charges, _time);
        bytes32 ch = generateStatusUsageHash(batteryId, _charges, _time);
        bool verified = false;

        if (batteryExists(bytes20(batteryId))) {
            if (!reused[ch]) {
                verified = true;
            }
        }

        address vendorId = vendorOf(bytes20(batteryId));

        return (verified, vendorId);
    }
}
