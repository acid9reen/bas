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

    // Returns true or false depending on whether it is registered
    // electric car with the specified address in the system or not.
    mapping (address => bool) public cars;

    // Returns true or false depending on whether it is registered
    // electric car with the specified address in the system or not.
    mapping (address => bool) public serviceCenters;

    //To notify the registration of a new manufacturer
    //  - account address from which registration took place
    //  - manufacturer identifier
    event Vendor(address owner, bytes4 tokenId);

    // To alert you when a new battery is created
    // - manufacturer identifier
    // - battery identifier
    event NewBattery(bytes4, bytes20);

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

    //Registers in the system the address of the sender of the transaction, as a service center.
    //Registration only occurs if this address has not already been registered
    //as a service center or electric car.
    function registerServiceCenter() public{
        require(!cars[msg.sender], "Service center have been already registered");
        require(!serviceCenters[msg.sender], "Service center have been already registered");
        serviceCenters[msg.sender] = true;
    }


    // Registers in the system the address of the sender of the transaction, an electric vehicle.
    // Registration only occurs if this address has not already been registered
    // as a service center or electric car.
    function registerCar() public payable{
        require(!cars[msg.sender], "Car have been already registered");
        require(!serviceCenters[msg.sender], "Car have been already registered");
        cars[msg.sender] = true;
    }

    // Sets new batFee
    function setFee(uint256 _batFee) public onlyOwner {
        batFee = _batFee;
    }

    //Gets batFee
    function getFee() public view returns(uint256){
        return batFee;
    }

}

