INSERT INTO branches VALUES (1,'HQ',NULL),(2,'North',1),(3,'South',1),(4,'North Annex',2);
INSERT INTO staff VALUES (10,1,'Ada'),(11,2,'Ben'),(12,3,'Cara'),(13,4,'Dev');
INSERT INTO customers VALUES (100,'Alpha','retail'),(101,'Beta','premier'),
                             (102,'Gamma','private'),(103,'Delta','retail');
INSERT INTO accounts VALUES (1000,2,250000,'open',NULL),(1001,2,50000,'open',NULL),
                            (1002,3,1200000,'open',NULL),(1003,4,0,'closed',13);
INSERT INTO account_holders VALUES (1000,100,'primary'),(1000,101,'joint'),
                                   (1001,101,'primary'),(1002,102,'primary'),
                                   (1002,100,'signatory'),(1003,103,'primary');
INSERT INTO transactions VALUES (5000,1000,15000,TRUE),(5001,1000,-2500,TRUE),
                                (5002,1001,7000,TRUE),(5003,1002,900000,TRUE),
                                (5004,1002,-100000,FALSE);
