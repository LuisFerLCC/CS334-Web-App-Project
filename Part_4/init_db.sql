PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
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
INSERT INTO Message VALUES(1,'Jean-Luc Picard','jlpicard@starfleet.gov','555-170-1002',replace('Good day,\n\nI find your tea selection most exhilarating. Please provide a sample of Earl Grey, hot.\nMake it so.','\n',char(10)));
INSERT INTO Message VALUES(2,'Eduardo Ceh-Varela','Eduardo.Ceh@enmu.edu',NULL,replace('Hello,\n\nPlease find below the order of presentations for the final project on Wednesday, May 7, from 12:30 pm to 2:30 pm.\nRemember that at least one of the team members must present the project.\nAs I have mentioned, it is not a technical presentation. You will have 10 minutes to show off your project and functionalities.\n\nI will give 5 extra points for the last stage to the team that presents the best overall project\nOur session will be via MS Teams.\n\nDo not forget to upload the final link for your work on Canvas. Remember that this is our final.\nLet me know if you have any questions','\n',char(10)));
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
INSERT INTO Status VALUES(0,'Cancelled');
INSERT INTO Status VALUES(1,'Pending');
INSERT INTO Status VALUES(2,'Preparing');
INSERT INTO Status VALUES(3,'Ready for delivery');
INSERT INTO Status VALUES(4,'Delivering');
INSERT INTO Status VALUES(5,'Completed');
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
INSERT INTO Series VALUES(1,'Black');
INSERT INTO Series VALUES(2,'Green');
INSERT INTO Series VALUES(3,'Latte');
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
INSERT INTO User VALUES(1,'Luis','Maldonado','lmaldonado@itpot.com','lmaldonado',0,1,1,0);
INSERT INTO User VALUES(2,'Marcus','Giannini','mgiannini@itpot.com','mgiannini',0,0,0,1);
INSERT INTO User VALUES(3,'Griffin','Graham','ggraham@itpot.com','ggraham',1,0,0,0);
INSERT INTO User VALUES(4,'Eduardo','Ceh-Varela','ecehvarela@itpot.com','ecehvarela',1,1,1,1);
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
INSERT INTO Item VALUES(1,'Cinnamon Circuit','A warm black tea blend with cinnamon and citrus notes.',0,0,50,3.49000000000000021,'product1.jpg',1);
INSERT INTO Item VALUES(2,'Matcha Byte','Smooth matcha latte with vanilla and honey.',0,0,50,2.49000000000000021,'product2.jpg',3);
INSERT INTO Item VALUES(3,'Debugger Detox','Refreshing green tea with mint and lemongrass.',1,0,50,2.99000000000000021,'product3.jpg',2);
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
INSERT INTO "Order" VALUES(1,'Luis','Maldonado','luisfern837@gmail.com','2025-04-29 23:36:25.000','1500 S Ave K, Portales, NM 88130','+52 (461) 138 1559',1);
INSERT INTO "Order" VALUES(2,'Mei','Reeder','Mei.Reeder@enmu.edu','2025-04-29 21:09:01','1500 S Ave K, Portales, NM 88130','575.562.1011',3);
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
INSERT INTO OrderedItems VALUES(1,1,2,'Extra Hot');
INSERT INTO OrderedItems VALUES(1,2,1,NULL);
INSERT INTO OrderedItems VALUES(2,3,1,NULL);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('User',4);
INSERT INTO sqlite_sequence VALUES('Message',2);
INSERT INTO sqlite_sequence VALUES('Status',5);
INSERT INTO sqlite_sequence VALUES('Series',3);
INSERT INTO sqlite_sequence VALUES('Item',3);
INSERT INTO sqlite_sequence VALUES('Order',2);
COMMIT;
