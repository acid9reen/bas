# Battery authentication system

Battery authentication system - это программное обеспечение призванное исключить возможность мошенничества со сторон участников сделки по замене аккумуляторных батарей в электромобиле. Предполагается что сделка проходит без участия человека, то есть станция по замене батареи и электромобиль могут быть полностью автономными.

## Установка
* [Установите go-ethereum](https://github.com/ethereum/go-ethereum)
* Установите используемые проектом библиотеки для Python

```bash
pip install -r requirements.txt
```

* Установите компилятор Solidity

```bash
python -m solc.install v0.6.4
```

* Скачайте исходный код с помощью HTTPS

```bash
git clone https://gitlab.com/acid9reen/bas.git
```

или SSH

```bash
git clone git@gitlab.com:acid9reen/bas.git
```

## Использование

### Для сущности разработчика программного обеспечения

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

### Для сущности производителя аккумуляторных батарей

#### Создание и регистрация аккаунта

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

### Для сущности сервисного центра

#### Создание аккаунта

```bash
python scenter.py --new <password>
```
Где *password* это пароль для создаваемого аккаунта

#### Регистрация аккаунта

```bash
python scenter.py --reg
```

### Для сущности электромобиля

#### Создание аккаунта

```bash
python car.py --new
```

#### Регистрация аккаунта

```bash
python car.py --reg
```