pragma solidity ^0.6.4;

import "./ServiceProviderWallet.sol";
import "./BatteryManagement.sol";
import "./lib/Ownable.sol";

contract ManagementContract is Ownable {

    ServiceProviderWallet public serviceProviderWallet;
    BatteryManagement public batteryManagement;
    uint256 batFee;

     //Deposit for each vendor
    mapping (address => uint256) public vendorDeposit;

    //Checking an already registered name
    mapping (bytes => bool) registeredVendor;

    //At the sender's address determines the name of the manufacturer that belongs to him
    mapping (address => bytes4) public vendorId;

    //By identifier returns the name of the manufacturer
    mapping (bytes4 => bytes) public vendorNames;

    //To notify the registration of a new manufacturer
    //  - account address from which registration took place
    //  - manufacturer identifier
    event Vendor(address owner, bytes4 tokenId);

    // To alert you when a new battery is created
    // - manufacturer identifier
    // - battery identifier
    event NewBattery(bytes4, bytes20);

    // Returns true or false depending on whether it is registered
    // electric car with the specified address in the system or not.
    mapping (address => bool) public cars;

    // Returns true or false depending on whether it is registered
    // electric car with the specified address in the system or not.
    mapping (address => bool) public serviceCenters;

    // Contract constructor
    // - address of the contract responsible for the accumulation of cryptocurrency,
    //    transferred as a deposit for using the service.
    // - the amount of the charge for the release of one battery
    constructor(address payable _serviceProviderWalletAddr, uint256 _batfee) public{
        batFee = _batfee;
        serviceProviderWallet = ServiceProviderWallet(_serviceProviderWalletAddr);
    }

    function setBatteryManagementContract(address _batteryMgmtContractAddr) public{
        batteryManagement = BatteryManagement(_batteryMgmtContractAddr);
    }

    function registerVendor(bytes memory _name) public payable{
        require(msg.value >= batFee * 1000, "Not enough money");
        require(!registeredVendor[_name], "Vendor have been already registered");
        require(vendorId[msg.sender] == '', "Vendor have been already registered");

        registeredVendor[_name] = true;

        bytes4 _nameSym = bytes4(keccak256(abi.encodePacked(msg.sender, _name, block.number)));

        vendorDeposit[msg.sender] += msg.value;
        address(serviceProviderWallet).transfer(msg.value);

        vendorId[msg.sender] = _nameSym;
        vendorNames[_nameSym] = _name;

        emit Vendor(msg.sender, _nameSym);
    }

    // Registers new batteries, if when calling the method on the balance
    // This manufacturer has enough funds. During registration
    // battery balance decreases according to the number of batteries and
    // The price currently set for this manufacturer.
    // - battery identifiers
    function registerBatteries(bytes20[]  memory _ids) public payable{
        uint _n = _ids.length;
        require(msg.value + vendorDeposit[msg.sender] >= _n * batFee, "Not enough money");

        bytes4 _tokenId = vendorId[msg.sender];
        require(_tokenId != "", "Vendor haven't been registered");

        vendorDeposit[msg.sender] += msg.value - (_n * batFee);
        if (msg.value > 0){
            address(serviceProviderWallet).transfer(msg.value);
        }

        for (uint i = 0; i < _n; i++){
            batteryManagement.createBattery(msg.sender, _ids[i]);
            emit NewBattery(_tokenId, _ids[i]);
        }

    }

    function registerCar() public payable{
        require(!cars[msg.sender], "Car have been already registered");
        require(!serviceCenters[msg.sender], "Car have been already registered");
        cars[msg.sender] = true;
    }

/*
    // Устанавливает адрес для контракта, ответственного за
    // управление информацией о батареях.
    // Доступен только создателю management контракта
    // - адрес контракта, управляющего инфорацией о батареях
    function setBatteryManagementContract(address) public;

    // Регистрирует вендора, если при вызове метода перечисляется
    // достаточно средств.
    // - наименование производителя
    function registerVendor(bytes20) public payable;

    // Возвращает размер текущий депозит вендора
    function vendorDeposit(address) public view returns(uint256);

    // Регистрирует новые батареи, если при вызове метода на балансе
    // данного производителя достаточно средств. Во время регистрации
    // батарей баланс уменьшается соответственно количеству батареи и
    // цене, установленной для данного производителя на текущий момент.
    // - идентификаторы батарей
    function registerBatteries(bytes20) public payable;

    // Возвращает наименование производителя по его идентификатору
    function vendorNames(bytes4) public view returns(bytes4);

    // Возвращает идентификатор производителя по адресу производителя
    function vendorId(address) public view returns(bytes4);

    // Возвращает адрес контракта, управляющего информацией о батареях,
    // установленного в данный момент.
    function batteryManagement() public view returns(address);

    // Устанавливает сумму сбора за выпуск одной батареи
    // - сумма сбора в wei
    function setFee(uint256) public;

    // Возвращает сумму сбора в wei, который будет списываться с депозита
    // за каждую выпущенную батарею. Если запрос идет от зарегистрированного
    // производителя батарей, то выдается та сумма сбора, которая была на момент
    // его регистрации.
    function batteryFee() public view returns(uint256);

    // Возвращает сумму сбора в wei, которую необходимо перечислить в качестве
    // депозита при регистрации производителя батарей. Сумма депозита
    // равна сумме за регистрацию 1000 батарей, что позволит защититься от
    // мошенников, поскольку требует серьезных вложений.
    function registrationDeposit() public view returns(uint256);

    // Возвращает адрес контракта, на котором происходит накопление
    // криптовалюты.
    function walletContract() public view returns(address);

    // Возвращает истину или ложь в зависимости от того, зарегистрирован сервис
    // центра с указанным адресом в системе или нет.
    function serviceCenters(address) public view returns(bool);

    // Регистрирует в системе адрес отправителя транзакции, как сервис центр.
    // Регистрация просиходит только если данный адрес уже не был зарегистрирован
    // в качестве сервис центра или электромобиля.
    function registerServiceCenter() public;

    // Возвращает истину или ложь в зависимости от того, зарегистрирован
    // электромобиль с указанным адресом в системе или нет.
    function cars(address) public view returns(bool);

    // Регистрирует в системе адрес отправителя транзакции, электромобиль.
    // Регистрация просиходит только если данный адрес уже не был зарегистрирован
    // в качестве сервис центра или электромобиля.
    function registerCar() public;
    */
}

