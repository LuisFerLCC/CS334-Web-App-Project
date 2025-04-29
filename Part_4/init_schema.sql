CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE Message
(
    MessageID  integer       not null
        constraint Message_pk
            primary key autoincrement,
    SenderName varchar(70)   not null,
    Email      varchar(50)   not null,
    Phone      varchar(18),
    Body       varchar(1000) not null,
    constraint Message_chk_Body_Length
        check (length(Message.Body) > 0),
    constraint Message_chk_Email_Format
        check (Message.Email LIKE '%@%.%'),
    constraint Message_chk_Phone_Length
        check (length(Message.Phone) >= 10),
    constraint Message_chk_SenderName_Length
        check (length(Message.SenderName) > 0)
);
CREATE TABLE Status
(
    StatusID integer     not null
        constraint Status_pk
            primary key autoincrement,
    Name     varchar(25) not null
        constraint Status_ck_Name
            unique,
    constraint Status_chk_Name_Length
        check (length(Status.Name) > 0)
);
CREATE TABLE Series
(
    SeriesID integer     not null
        constraint Series_pk
            primary key autoincrement,
    Name     varchar(30) not null
        constraint Series_ck_Name
            unique,
    constraint Series_chk_Name_Length
        check (length(Series.Name) > 0)
);
CREATE TABLE User
(
    UserID           integer               not null
        constraint User_pk
            primary key autoincrement,
    FirstName        varchar(30)           not null,
    LastName         varchar(30)           not null,
    Email            varchar(50)           not null
        constraint User_ck_Email
            unique,
    Password         varchar(30)           not null,
    ManagesOrders    boolean default false not null,
    ManagesInventory boolean default false not null,
    ManagesMessages  boolean default false not null,
    ManagesUsers     boolean default false not null,
    constraint User_chk_Email_Format
        check (User.Email LIKE '%@%.%'),
    constraint User_chk_FirstName_Length
        check (length(User.FirstName) > 0),
    constraint User_chk_LastName_Length
        check (length(User.LastName) > 0),
    constraint User_chk_Manages_AtLeastOne
        check (User.ManagesOrders OR User.ManagesInventory OR User.ManagesMessages OR User.ManagesUsers),
    constraint User_chk_Password_Length
        check (length(User.Password) >= 6)
);
CREATE TABLE Item
(
    ItemID       integer               not null
        constraint Item_pk
            primary key autoincrement,
    Name         varchar(30)           not null,
    Description  varchar(65)           not null,
    IsNoCaffeine boolean default false not null,
    IsCold       boolean default false not null,
    Stock        integer               not null,
    Price        float                 not null,
    ImageURL     varchar(50)           not null
        constraint Item_ck_ImageURL
            unique,
    SeriesID     integer               not null
        constraint Item_fk_SeriesID
            references Series,
    constraint Item_chk_Description_Length
        check (length(Item.Description) > 0),
    constraint Item_chk_ImageURL_Length
        check (length(Item.ImageURL) > 0),
    constraint Item_chk_Name_Length
        check (length(Item.Name) > 0),
    constraint Item_chk_Price_IsPositive
        check (Item.Price > 0),
    constraint Item_chk_Stock_IsNotNegative
        check (Item.Stock >= 0)
);
CREATE TABLE IF NOT EXISTS "Order"
(
    OrderID           integer                            not null
        constraint Order_pk
            primary key autoincrement,
    CustomerFirstName varchar(30)                        not null,
    CustomerLastName  varchar(30)                        not null,
    Email             varchar(50)                        not null,
    DateTime          datetime default CURRENT_TIMESTAMP not null,
    Address           varchar(100)                       not null,
    Phone             varchar(18)                        not null,
    StatusID          integer  default 1                 not null
        constraint Order_fk_StatusID
            references Status,
    constraint Order_chk_Address_Length
        check (length("Order".Address) > 0),
    constraint Order_chk_CustomerFirstName_Length
        check (length("Order".CustomerFirstName) > 0),
    constraint Order_chk_CustomerLastName_Length
        check (length("Order".CustomerLastName) > 0),
    constraint Order_chk_Email_Format
        check ("Order".Email LIKE '%@%.%'),
    constraint Order_chk_Phone_Length
        check (length("Order".Phone) >= 10)
);
CREATE TABLE OrderedItems
(
    OrderID             integer not null
        constraint OrderedItems_fk_OrderID
            references "Order"
            on update cascade on delete cascade,
    ItemID              integer not null
        constraint OrderedItems_fk_ItemID
            references Item
            on update cascade on delete restrict,
    Amount              integer not null,
    SpecialInstructions varchar(100),
    constraint OrderedItems_pk
        primary key (OrderID, ItemID),
    constraint OrderedItems_chk_Amount_IsPositive
        check (OrderedItems.Amount > 0),
    constraint OrderedItems_chk_SpecialInstructions_Length
        check (length(OrderedItems.SpecialInstructions) > 0)
);
