* 1. uzd;
libname BIBL "/home/u62272156/lab1";
run;

*2. uzd;
DATA BIBL.pard;
INPUT Nr $ Valiuta $ Suma 7.2;
DATALINES;
101 USA 3295.50
3034 EUR 1876.30
101 USA 2938.00
128 USA 2908.74
1345 EUR 3145.60
109 USA 2789.10
;

*3 uzd;
DATA bibl.flights ;
INFILE "/home/u62272156/lab1/sfosch.dat";
INPUT FLightID $ 1-7 
	  RouteID $ 8-14
	  Destination $ 18-20
	  Model $ 21-40
	  DepartDay 51
	  TotPassCap 65-67
;

PROC PRINT data=bibl.flights(obs=8);
title 'Pavadinimo testas';
footnote "Komentaros testas";

DATA bibl.flights2;
infile "/home/u62272156/lab1/sfosch.dat";
input FlightID $ 1-7
	  RouteID $ 8-14
	  Destination $ 18-20
	  Model $ 21-40
	  @41 Date date9.
	  TotalPassCap 65-67
;


PROC PRINT data=bibl.flights2(obs=5);
format Date date9. ;

PROC PRINT data=bibl.flights2(obs=10) label;
label FlightID=' FlightID'
	  Destination= 'TESTAS'
;

*???? uzd;
DATA bibl.flights3;
infile "/home/u62272156/lab1/sfosch.dat";
input FlightID $ 1-7
	  RouteID $ 8-14
	  Destination $ 18-20
	  Model $ 21-40
	  @41 Date date9.
	  TotalPassCap 65-67
;

*4 uzd;
PROC IMPORT OUT= bibl.flights3
 DATAFILE=
"/home/u62272156/lab1/sfoschdates.xls"
 DBMS=XLS REPLACE;
 SHEET="SFODATA";
 GETNAMES=YES;
RUN;

*5 uzd;
DATA bibl.flights4;
SET bibl.flights3;
keep FlightID RouteID Destination Model DepartDay TotPassCap;

*6 uzd;
PROC CONTENTS;

PROC CONTENTS DATA=bibl.flights2;

*7 uzd;
DATA bibl.passngrs; 
  set "/home/u62272156/lab1/passngrs.sas7bdat"; 
RUN; 

PROC PRINT data=bibl.passngrs;
title 'passengers';
sum FClass;
sum BClass;
sum EClass;

PROC PRINT data=bibl.passngrs noobs;
title 'passengers';
WHERE
Dest='SEA' and EClass >= 102 and BClass < 11.5;


DATA laikinas;
set bibl.passngrs;
keep FlightID Depart EClass;

PROC PRINT data=laikinas;
title 'passengers';

proc means data=bibl.passngrs n mean max min;
   var FClass BClass EClass;
   title 'Summary';
   class Dest;
run;

* 8 uzd.;
DATA bibl.fltattnd; 
  set "/home/u62272156/lab1/fltattnd.sas7bdat"; 
RUN;

DATA RAISES;
set bibl.fltattnd;
BonusAMT = Salary*0.03;
Mon = MONTH(HireDate);
format Salary DOLLAR7.;
format BonusAMT DOLLAR7.;
keep EmpID Salary BonusAmt HireDate Mon;
RUN;

PROC PRINT data=RAISES(obs=5);
title '8uzd';

* 9 uzd;
DATA RAISES;
set bibl.fltattnd;
IF JobCode='FLTAT1' then
	Increase = 0.13 * Salary;
IF JobCode='FLTAT2' then
	Increase = 0.08 * Salary;
IF JobCode='FLTAT3' then
	Increase = 0.03 * Salary;
NewSal = Salary + Increase;
format Salary DOLLAR7.;
format Increase DOLLAR7.;
format NewSal DOLLAR7.;
keep EmpID Salary Increase NewSal;
RUN;

* 10 uzd;
DATA RAISES;
set bibl.fltattnd;
IF JobCode='FLTAT1' then
	Increase = 0.13 * Salary;
IF JobCode='FLTAT2' then
	Increase = 0.08 * Salary;
IF JobCode='FLTAT3' then
	Increase = 0.03 * Salary;
	
IF JobCode='FLTAT1' then
	BonusAMT = 0.12 * Salary;
IF JobCode='FLTAT2' then
	BonusAMT = 0.09 * Salary;
IF JobCode='FLTAT3' then
	BonusAMT = 0.07 * Salary;

NewSal = Salary + Increase;
format Salary DOLLAR7.;
format Increase DOLLAR7.;
format NewSal DOLLAR7.;
format BonusAmt DOLLAR7.;
keep EmpID Salary Increase NewSal BonusAmt;
RUN;

data RAISES;
set RAISES;
where BonusAMT >  1000;
run;

PROC PRINT data=RAISES(obs=5);
title '10uzd';

*11 uzd.;
DATA RAISES;
set bibl.fltattnd;
length JobTitle $ 30;
IF JobCode='FLTAT1' then
	do;
	Increase = 0.13 * Salary;
	JobTitle = 'Flight attendant I';
	end;
IF JobCode='FLTAT2' then
	do;
	Increase = 0.08 * Salary;
	JobTitle = 'Flight attensdant II';
	end;
IF JobCode='FLTAT3' then
	do;
	Increase = 0.03 * Salary;
	JobTitle = 'Senior flight attendant';
	end;
NewSal = Salary + Incease;
format Salary DOLLAR7.;
format Increase DOLLAR7.;
format NewSal DOLLAR7.;
keep EmpID JobCode JobTitle Salary Increase NewSal;
RUN;
