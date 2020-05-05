pragma solidity ^0.6.4;
import "./BatteryManagement.sol";
import "./ManagementContract.sol";

contract Deal {
    BatteryManagement public batteryManagement;
    ManagementContract public managementContract;
    bytes20 oldBat;
    bytes20 newBat;
    address erc20Token;
    uint256 ammortizedFee;
    uint256 serviceFeeValue;
    uint256 timeout;
    uint256 deal_state;

    // Конструктор контракта
    // _oldBat - идентификатор старой батареи
    // _newBat - идентификатор новой батареи
    // _erc20Token - адрес контракта расчетных токенов
    // _ammorFee - количество токенов, определяющих компенсацию амортизации батарей
    // - количество токенов, определяющих выполнение работ по замене
    // - временной промежуток, в ходе которого запрещено разблокирование
    // расчетных токенов.
    constructor(bytes20 _oldBat, bytes20 _newBat, address _erc20Token, uint256 _ammorFee, uint256 _serviceFee, uint256 _timeout) public {
        oldBat = _oldBat;
        newBat = _newBat;
        erc20Token = _erc20Token;
        ammortizedFee = _ammorFee;
        serviceFeeValue = _serviceFee;
        timeout = _timeout;
        deal_state = 1;
        batteryManagement = BatteryManagement(msg.sender);
        managementContract = ManagementContract(batteryManagement.managementContract());
    }

    // Возвращают идентификаторы батарей, вовлеченных в контракт.
    function oldBattery() public view returns(bytes20) {
        return oldBat;
    }

    function newBattery() public view returns(bytes20) {
        return newBat;
    }
    // Возвращают информацию о батареях, вовлеченных в контракт.
    // Возвращаемые значения:
    // - количество зарядов
    // - идентификатор производителя
    // - наименование производителя
    function oldBatteryInfo() public view returns(uint256, bytes4, bytes memory)
    {
        uint256 charges = batteryManagement.chargesNumber(oldBat);
        address vendorAddress = batteryManagement.vendorOf(oldBat);
        bytes4 vendorId = managementContract.vendorId(vendorAddress);

        return (charges, vendorId, getVendorNamesByChunks(vendorId));
    }

    function newBatteryInfo() public view returns(uint256, bytes4, bytes memory) {
        uint256 charges = batteryManagement.chargesNumber(newBat);
        address vendorAddress = batteryManagement.vendorOf(newBat);
        bytes4 vendorId = managementContract.vendorId(vendorAddress);

        return (charges, vendorId, getVendorNamesByChunks(vendorId));
    }

    // Возвращает количество токенов, определяющих компенсацию амортизации
    // батарей
    function deprecationValue() public view returns(uint256) {
        return ammortizedFee;
    }

    // Возвращает количество токенов, определяющих выполнение работ по
    // замене
    function serviceFee() public view returns(uint256) {
        return serviceFeeValue;
    }

    // Возвращает текущий статус контракта
    // 1 - Ожидание согласия со сделкой от автомобиля
    // 2 - Согласие со сделкой получено
    // 3 - Оплата работ выполнена
    function state() public view returns(uint256) {
        return deal_state;
    }


    // Перепосылает аргументы в контракт BatteryManagement для проверки цифровой
    // подписи. Возвращаемый результат проверки такой же, как и в оригинальной
    // функции: 0 - результат проверки цифровой подписи, показывает
    // что она сделана батареей, для которой существует токен; 1 - транзакция
    // с таким статусом уже отправлялась в блокчейн, что указывает на возможную
    // прослушку траффика; 2 - для батареи нет соответствующего токена; 999 -
    // другая ошибка.
    // - число зарядов
    // - временная метка
    // - v, r, s компоненты цифровой подписи
    function verifyBattery(uint256 charges, uint256 time, uint8 v, bytes32 r, bytes32 s)
    public view returns(bool, address){
        return batteryManagement.verifyBattery(v, r, s, charges, time);
    }

    function getVendorNamesByChunks(bytes4 _id) public view returns(bytes memory){
        uint256 l = managementContract.vendorNamesDataLen(_id);
        bytes memory data = new bytes(l);

        uint256 pos = 0;

        for(uint256 i = 0; i < (l / 32) + 1; i++) {
            bytes32 d = managementContract.vendorNamesDataChunk(_id, i);
            uint256 j = 0;

            while(j < 32 && j + pos < l) {
                data[pos+j] = d[j];
                j++;
            }
            pos = pos + j;
        }
        return(data);
    }
}
