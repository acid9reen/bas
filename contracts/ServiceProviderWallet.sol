pragma solidity 0.6.4;

import './lib/Ownable.sol';

contract ServiceProviderWallet is Ownable {
    // Для оповещения поступлении новых средств
    // - адрес, с которого перечислены средства
    // - сумма поступления
    event Received(address, uint256);

    // Для оповещения о выдачи части средств
    // - адрес, какой инициировал выдачу средств
    // - адрес, на который направлены средства
    // - сумма к выдаче
    event Withdraw(address, address, uint256);

    receive() external payable {
        require(msg.value > 0, "Negative value!");
        emit Received(msg.sender, msg.value);
    }

    // Используется для выдачи части средств с адреса контаркта
    function withdraw(address payable _to, uint256 _value) external onlyOwner{
        _to.transfer(_value);
        emit Withdraw(msg.sender, _to, _value);
    }

    // Позволяет удалить контракт
    function kill() external onlyOwner{
        require(msg.sender == owner);
        selfdestruct(msg.sender);
    }
}
