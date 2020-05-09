# Battery authentication system

Battery authentication system - это программное обеспечение призванное исключить возможность мошенничества со сторон участников сделки по замене аккумуляторных батарей в электромобиле. Предполагается что сделка проходит без участия человека, то есть станция по замене батареи и электромобиль могут быть полностью автономными.

## Установка
1. [Установите python](https://www.python.org/)
2. [Установите go-ethereum](https://github.com/ethereum/go-ethereum)
3. Установите используемые проектом библиотеки для Python

```bash
pip install -r requirements.txt
```

4. Установите компилятор Solidity

```bash
python -m solc.install v0.6.4
```

5. Скачайте исходный код с помощью HTTPS

```bash
git clone https://gitlab.com/acid9reen/bas.git
```

или SSH

```bash
git clone git@gitlab.com:acid9reen/bas.git
```

## Использование

* ### Для сущности разработчика программного обеспечения

#### Создание аккаунта

```bash
python setup.py --new <password>
```
Где *password* это пароль для создаваемого аккаунта

#### Настройка смарт контрактов и их регистрация в сети блокчейн

```bash
python setup.py --setup <service fee>
```
Где *service fee* это цена за регистрацию одной батареи в eth

#### Изменение сборов за регистрацию одной батареи

```bash
python setup.py --setfee <service fee>
```
Где *service fee* это цена за регистрацию одной батареи в eth

* ### Для сущности производителя аккумуляторных батарей

#### Создание аккаунта

```bash
python vendor.py --new <password>
```
Где *password* это пароль для создаваемого аккаунта


#### Регистрация аккаунта

```bash
python vendor.py --reg <vendor name> <service fee>
```
Где *vendor name* это наименование производителя батарей  
*service fee* - размер депозита в eth для регистрации производителя

#### Регистрация батарей в сети блокчейн

```bash
python vendor.py --bat <quantity> [<deposit>]
```
Где *quantity* это количество батарей для регистрации  
*deposit* - сумма в eth для пополнения депозита производителя

#### Получение информации о стоимости регистрации производителя

```bash
python vendor.py --regfee
```

#### Получение информации о стоимости регистрации одной батареи

```bash
python vendor.py --batfee
```

#### Продажа батареи сервисному центру или автомобилю при производстве

```bash
python vendor.py --owner <battery_id> <new_owner>
```

Где *battery_id* это идентификатор батареи
*new_owner* - покупатель батареи

#### Получение остатка по депозиту

```bash
python vendor.py --deposit
```

* ### Для сущности сервисного центра

#### Создание аккаунта

```bash
python scenter.py --new <password>
```
Где *password* это пароль для создаваемого аккаунта

#### Регистрация аккаунта

```bash
python scenter.py --reg
```

#### Верификация батареи

```bash
python scenter.py --verify <battery_id>
```
Где *battery_id* - идентификатор батареи

* ### Для сущности электромобиля

#### Создание аккаунта

```bash
python car.py --new
```

#### Регистрация аккаунта

```bash
python car.py --reg
```

#### Верификация батареи

```bash
python scenter.py --verify <battery_id>
```
Где *battery_id* - идентификатор батареи

#### Инициализация сделаки

```bash
python scenter.py --initiate_replacement <car_battery_id> <sc_battery_id>
```
Где *car_battery_id* - идентификатор батареи электромобиля
*sc_battery_id* - идентификатор батареи сервисного центра