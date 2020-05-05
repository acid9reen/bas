pragma solidity ^0.6.4;

import "./ManagementContract.sol";
import "./ERC20Token.sol";
import "./lib/Ownable.sol";
import "./NFT/BasicNFToken.sol";
import "./lib/SafeMath.sol";
import "./Deal.sol";

contract Fee {
    // Для хранения минимальных компенсаций в зависимости
    // от разницы количества зарядок батарей
    mapping (uint256 => uint256) public minimalFees;

    // Для хранения минимальных компенсаций в зависимости
    // от разницы количества зарядок батарей
    mapping (uint256 => uint256) public maximalFees;

    function setMinimalFees(uint256[] memory _fees, uint counter) public {
        for (uint i = counter; (i < (_fees.length) + counter); i++) {
            minimalFees[i] = _fees[i-counter];
        }
    }


    function setMaximalFees(uint256[]  memory _fees, uint counter) public {
        for (uint i = counter; (i < (_fees.length) + counter); i++) {
            maximalFees[i] = _fees[i-counter];
        }
    }
}

contract BatteryManagement is Ownable, BasicNFToken{
    ManagementContract public managementContract;
    ERC20Token public erc20Token;// Контракт для хранения амортизационной комиссии
    Fee public fees;

    mapping (bytes20 => uint256) public chargesNumber;

    uint256 timeout = 3600;

    //Checking if car has battery
    mapping (address => bool) carHasBattery;

    // Для проверки на повторное использование транзакции
    mapping (bytes32 => bool) reused;

    // Для проверки на участие батареи в другом контракте
    mapping (bytes20 => bool) isUsed;

    // To notify the transfer of battery ownership to a new ownerдельцу
    // from - address of the previous owner
    // to - address of the new owner
    // batteryId - battery identifier
    event Transfer(address from, address to, bytes20 batteryId);

    // Для оповещения после создания контракта на замену батарей
    // - адрес контракта
    event NewDeal(address newDeal);


    // Contract constructor
    // - The address of the contract managing the list of vendors.
    // - address of the contract that manages the tokens in which it will be
    //    Settlement for battery replacement.
    constructor(address _mgmt, address _erc20Token) public {
        managementContract = ManagementContract(_mgmt);
        erc20Token = ERC20Token(_erc20Token);
        fees = new Fee();

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

    // Returns the address of the battery manufacturer
    // _batteryId - battery identifier
    function vendorOf(bytes20 _batteryId) public view returns(address){
        return tokenID[_batteryId];
    }


    // Calculates the hash used to check for repeated
    // use of transaction
    // _addr - address obtained from the signature and transaction hash
    // _charges - amount of battery charge
    // _time - time for receiving battery information
    function generateStatusUsageHash(address _addr, uint256 _charges, uint256 _time)
    internal pure returns (bytes32){
        return keccak256(abi.encodePacked(_addr, _charges, _time));
    }


    // Verifies the digital signature for the data and returns the result
    // checks (True - if the battery exists, False - if not) and the vendor address.
    // _v, _r, _s - v, r, s digital signature components
    // _charges - number of charges
    // _time - timestamp
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

    // Проверяет батарею предоставленную машиной
    function verifyOldBattery(uint256 _p, bytes32 _r1, bytes32 _s1, address _car) internal returns(bytes20) {
        uint256 p = _p;

        uint256 charges = SafeMath.div(_p, 2**160);
        p %= 2**160;
        uint256 time = SafeMath.div(_p, 2**128);
        p %= 2**128;
        uint256 v = SafeMath.div(_p, 2**96);
        p %= 2**96;

        require(managementContract.cars(_car), "");

        bool oldBatteryValidity;
        address oldBatteryVendorAddress;
        (oldBatteryValidity, oldBatteryVendorAddress) = verifyBattery(uint8(v), _r1, _s1, charges, time);

        require(oldBatteryValidity, "");

        address oldBatteryId = getBatteryIdFromSignature(uint8(v), _r1, _s1, charges, time);

        require(tokenIdToOwner[bytes20(oldBatteryId)] == _car, "");
        require(carHasBattery[_car], "");
        require(!isUsed[bytes20(oldBatteryId)], "");

        chargesNumber[bytes20(oldBatteryId)] = charges;

        return(bytes20(oldBatteryId));
    }

    function verifyNewBattery(uint256 _p, bytes32 _r2, bytes32 _s2) internal returns(bytes20) {
        uint256 p = _p;
        uint256 charges = SafeMath.div(_p, 2**64);
        p %= 2**64;
        uint256 time = SafeMath.div(_p, 2**32);
        p %= 2**32;
        uint256 v = p;

        require(managementContract.serviceCenters(msg.sender), "");

        bool newBatteryValidity;
        address newBatteryVendorAddress;
        (newBatteryValidity, newBatteryVendorAddress) = verifyBattery(uint8(v), _r2, _s2, charges, time);

        require(newBatteryValidity, "");

        address newBatteryId = getBatteryIdFromSignature(uint8(v), _r2, _s2, charges, time);

        require(tokenIdToOwner[bytes20(newBatteryId)] == msg.sender, "");
        require(carHasBattery[msg.sender], "");
        require(!isUsed[bytes20(newBatteryId)], "");

        chargesNumber[bytes20(newBatteryId)] = charges;

        return bytes20(newBatteryId);
        }

    // Расчитывает амортизационную стоимость при замене батареи
    function getAmortizedFee(uint256 _oldBattery, uint256 _newBattery) internal view returns(uint256){
        if (_newBattery >= 300) {
            return 0;
        } else if (_oldBattery >= 300) {
            return 1000;

        } else if (_newBattery >= 150) {
            return _oldBattery - _newBattery;

        } else if (_newBattery >= 50) {
            if (_oldBattery >= 150){
                return fees.minimalFees(_oldBattery - _newBattery);
            }
            else {
                return _oldBattery - _newBattery;}
        } else if (_oldBattery >= 150) {
            return fees.maximalFees(_oldBattery - _newBattery);

        }else if (_oldBattery >= 50) {
            return fees.minimalFees(_oldBattery - _newBattery);

        } else {
            return _oldBattery - _newBattery;
        }
    }


    // Получает значение из упакованных данных с необходимым сдвигом
    function getValueFromPack(uint256 _p, uint256 _power) internal pure returns(uint256) {
        return SafeMath.div(_p, _power);
    }


    // Делегирует право аккаунту изменять владельца для токена, которым на текущий
    // момент владеет аккаунт-отправитель транзакции. Может выполняться, если
    // аккаунт-отправитель тразанкции действительно владеет данным токенов. Для
    // одного токена может быть только один делегат. Для отзыва права необходимо
    // послать 0 в качестве адреса.
    // Генерирует событие Approval.
    // - адрес делегата
    // - идентификатор токена
    function approve(address _to, bytes20 _tokenId) public{
    require(tokenIdToOwner[_tokenId] == msg.sender, "");
    _approve(_to,_tokenId);
    }


    // Forms a new contract for battery replacement operations.
    // The contract identifies the battery identifiers involved in the transaction,
    // car account address, battery depreciation compensation amount,
    // amount for completion of replacement work.
    // Battery identifiers become known through digital verification.
    // signatures for battery statuses.
    // The amount of compensation is calculated depending on the amount of charge,
    // transferred in battery status.
    // The contract should not be created if for batteries with such
    // identifiers there is no corresponding token if one of the batteries
    // already participating in some other replacement contract or contract participants
    // do not own batteries.
    // _p - packed data storing the status of two batteries at once. Packaging
    // data is used to reduce gas used for data,
    // transferred in transactions to the contract method. Packing method:
    // p = n1 * (2 ** 160) + t1 * (2 ** 128) + v1 * (2 ** 96) + n2 * (2 ** 64) + t2 * (2 ** 32) + v2
    // _r1 - r signature component for old battery data
    // _s1 - s signature component for old battery data
    // _r2 - r signature component for new battery data
    // _s2 - s signature component for new battery data
    // _car - car account address
    // _scenterFee - the number of settlement tokens that determine the replacement work
    function initiateDeal(uint256 _p, bytes32 _r1, bytes32 _s1, bytes32 _r2, bytes32 _s2, address _car, uint256 _scenterFee) public {
        {
        uint256 p = _p;
        bytes20 oldBatteryId = verifyOldBattery(_p, _r1, _s1, _car);
        bytes20 newBatteryId = verifyNewBattery(_p % (2**96), _r2, _s2);
        uint256 amortizedFee = getAmortizedFee(getValueFromPack(p, 2**160), getValueFromPack(p % (2**96), 2**64));

        Deal deal = new Deal(oldBatteryId, newBatteryId, address(erc20Token), amortizedFee, _scenterFee, timeout);
        isUsed[oldBatteryId] = true;
        isUsed[newBatteryId] = true;
        reused[generateStatusUsageHash(address(oldBatteryId), getValueFromPack(p, 2**160), getValueFromPack(p % (2**160), 2**128))] = true;
        reused[generateStatusUsageHash(address(newBatteryId), getValueFromPack(p % 2**96, 2**64), getValueFromPack(p % 2**64, 2**32))] = true;
        approve(address(deal), newBatteryId);

        emit NewDeal(address(deal));
}

    }
}
