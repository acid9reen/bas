pragma solidity ^0.6.4;

contract BatteryManagement {
    // Для оповещения о передаче прав владения батареей новому владельцу
    // - адрес предыдущего владельца
    // - адрес нового владельца
    // - индентификатор батареи
    event Transfer(address indexed, address indexed, bytes20);

    // Для оповещения, что какому-то аккунту делегировано право менять владельца
    // батареи
    // - владелец батареи
    // - адрес далегата
    // - идентификатор батареи, которой может распоряжаться делегат
    event Approval(address indexed, address indexed, bytes20);

    // Для оповещения после создания контракта на замену батарей
    // - адрес контракта
    event NewDeal(address);

    // Конструктор контракта
    // - адрес контракта, управляющего списком вендоров.
    // - адрес контракта, управляющего токенами, в которых будет
    //   происходить расчет за замену батарей.
    constructor(address, address) public {}

    // Создает новую батарею
    // Владельцем батареи назначается его текущий создатель.
    // Создание нового батареи может быть доступно только
    // management контракту
    // - адрес производителя батареи
    // - идентификатор батареи
    function createBattery(address, bytes20) public;

    // Меняет владельца батареи. Может быть вызвана только
    // текущим владельцем
    // - адрес нового владельца
    // - идентификатор батареи
    function transfer(address, bytes20) public;

    // Меняет владельца для всех батарей перечисленных в списке. Может быть вызвана
    // только текущим владельцем
    // - адрес нового владельца
    // - список идентификаторов батарей
    function transfer(address, bytes20[]) public;

    // Определяет по статусу батареи ее идентификатор, затем текущего владельца.
    // И меняет владельца батаереи. Может быть вызвана только текущим владельцем
    // - запакованные данные, хранящие статус батареи и нового получателя. Упаковка
    //   данных используется для уменьшения используемого газа за данные,
    //   передаваемые в транзакции в метод контракта. Метод упаковки:
    //   p = n*(2**124) + t*(2**192) + v*(2**160) + address
    // - r компонента подписи для данных батареи
    // - s компонента подписи для данных батареи
    function transfer(bytes32, bytes32, bytes32) public;

    // Делегирует право аккунту изменять владельца батареи, которой на текущий
    // момент владеет аккаунт-отправитель транзакции. Может выполняться, если
    // аккаунт-отправитель тразанкции действительно владеет данной батареей. Для
    // одной батареи может быть только один делегат. Для отзыва права необходимо
    // послать 0 в качестве адреса.
    // Генерирует событие Approval.
    // - адрес делегата
    // - идентификатор батареи
    function approve(address, bytes20) public;

    // Делегирует право аккунту изменять владельца батареи, которым на текущий
    // момент владеет аккаунт, адрес которого определяется в ходе проверки цифровой
    // подписи. Может выполняться, если аккаунт, восстанавливаемый из цифровой
    // подписи, действительно владеет данной батареей. Для одной батареи может
    // быть только один делегат. Для отзыва права необходимо
    // послать 0 в качестве адреса.
    // Цифровая подпись проверяется относительно адреса отправителя транзакции
    // (msg.sender), поскольку подразумевается, что тем самым владелец батареи
    // подтверждает, что делегирование права может быть выполнено с данного адреса.
    // Генерирует событие Approval.
    // - адрес делегата
    // - идентификатор батареи
    // - v, r, s компоненты цифровой подписи
    function delegatedApprove(address, bytes20, uint8, bytes32, bytes32) public;

    // Меняет владельца батареи. Может выполняться, только если отправителю
    // транзакций делегировано право изменения владельца для данной батареи.
    // Генерирует событие Transfer.
    // - адрес владельца батареи
    // - адрес получателя
    // - идентификатор батареи
    function transferFrom(address, address, bytes20) public;

    // Возвращает адрес текущего зарегистрированного владельца батареи
    // - индентификатор батареи
    function ownerOf(bytes20) public view returns(address);

    // Возвращает адрес производителя батареи
    // - идентификатор батареи
    function vendorOf(bytes20) public view returns(address);

    // Проверяет цифровую подпись для данных и возвращает результат
    // проверки и адрес вендора.
    // Результат проверки: 0 - результат проверки цифровой подписи, показывает
    // что она сделана зарегистрированной батареей; 1 - транзакция
    // с таким статусом уже отправлялась в блокчейн, что указывает на возможную
    // прослушку траффика; 2 - нет соответствующей зарегистрированной батареи;
    // 999 - другая ошибка.
    // - число зарядов
    // - временная метка
    // - v, r, s компоненты цифровой подписи
    function verifyBattery(uint256 n, uint256 t, uint8 v, bytes32 r, bytes32 s) public view returns(uint256, address);

    // Формирует новый контракт на выполнение операций по замене батарей.
    // В контракт передаются идентификаторы батарей, участвующие в сделке,
    // адрес аккаунта автомобиля, сумма на компенсацию амортизации батарей,
    // сумма за выполенние работ по замене.
    // Идентификаторы батарей становятся известны в ходе проверки цифровых
    // подписей для статусов батарей.
    // Сумма компенсации исчисляется в зависимости от количества заряда,
    // переданного в статусе батарей.
    // Контракт не должен создаваться, если для батареи с такими
    // идентфикаторами не зарегистрированы в контракте, если одна из батарей
    // уже участвует в каком-то другом контракте замены или участники контракта
    // не являются владельцами батарей.
    // - запакованные данные, хранящие статус сразу двух батарей. Упаковка
    //   данных используется для уменьшения используемого газа за данные,
    //   передаваемые в транзакции в метод контракта. Метод упаковки:
    //   p = n1*(2**160) + t1*(2**128) + v1*(2**96) + n2*(2**64) + t2*(2**32) + v2
    // - r компонента подписи для данных старой батареи
    // - s компонента подписи для данных старой батареи
    // - r компонента подписи для данных новой батареи
    // - s компонента подписи для данных новой батареи
    // - адрес аккаунта автомобиля
    // - количество расчетных токенов, определяющих выполнение работ по замене
    function initiateDeal(uint256, bytes32, bytes32, bytes32, bytes32, address, uint256) public;

    // Возвращает количество зарядов для конкретной батареи, зарегистрированных
    // в данный момент
    // - идентификатор батареи
    function chargesNumber(bytes20) public view returns(uint256);

    // Извлекает из переданных данных цифровую подпись текущего владельца батареи,
    // адрес нового владельца батареи, ее статус. Изменяет владельца, если
    // нет нарущений прав владения для восстановленного из подпсис адреса.
    // - запакованные данные, хранящие статус батареи и нового получателя. Упаковка
    //   данных используется для уменьшения используемого газа за данные,
    //   передаваемые в транзакции в метод контракта. Метод упаковки (от старших
    //   байт к младшим):
    //    0..3   байт - число зарядов
    //    4..7   байт - временная метка
    //    8..75  байт - v, r, s компоненты цифровой подписи статуса батареи
    //   76..95  байт - адрес нового владельца
    //   96..163 байт - v, r, s компоненты цифровой подписи текущего владельца
    function approvedTransfer(bytes20) public;

    // Проверяет переданный адрес, если он является контрактом сделки.
    // Возрващает 0 - контракт сделки существует и аккаунт, с которого
    // осуществляется запрос, является участником сделки; 1 - контракт сделки
    // существует, но аккаунт не является участников сделки; 2 - контракт
    // сделки не существует.
    function checkDealContract(address) public view returns(uint256);

    // Устанавливает верменной промежуток, после которого разрешено
    // разблокирование расчетных токенов контрактом сделки. Данная операция
    // разрешена только аккаунту производителя ПО.
    // - размер временного промежутка в секундах.
    function setTimeoutThreshold(uint256) public;

    // Возвращает временной промежуток, запрета разблокирования расчетных
    // токенов, установленный на текущий момент.
    function timeoutThreshold() public view returns(uint256);

    // Возвращает адрес контракта, который управляет регистрацией производителей
    // батарей.
    function managementContract() public view returns(address);

    // Возвращает адрес контракта, который управляет токенами, использующимися
    // в качестве внутренней валюты при совершении сделок по замене батарей.
    function erc20() public view returns(address);
}
