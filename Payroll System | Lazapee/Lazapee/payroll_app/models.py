from typing import Any
from django.db import models
import calendar

overtime = []

class Employee(models.Model):
    name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=6, unique=True)
    rate = models.FloatField()
    overtime_hours = models.FloatField(blank=True, null=True, default=0)
    overtime_pay = models.FloatField(blank= True, null = True, default=0)
    allowance = models.FloatField(blank = True, null = True, default=0)

    def getName(self):
        return self.name
    def getID(self):
        return self.id_number
    def getRate(self):
        if self.rate < 0: 
            self.rate = 0 
        return self.rate
    def getOvertimeHours(self):
        return self.overtime_hours
    def getOvertimePay(self):
        self.overtime_pay = (self.rate/160) * 1.5 * self.overtime_hours
        self.overtime_pay=round(self.overtime_pay,2)
        return self.overtime_pay
    def resetOvertime(self):
        self.overtime_hours = 0
        self.getOvertimePay()
        self.save()
        return self.overtime_pay
    def getAllowance(self):
        return self.allowance  
    def __str__(self):
        return f"pk: {self.id_number}, rate: {self.rate}"
    
class Payslip(models.Model):
    id_number = models.ForeignKey(Employee, to_field='id_number', on_delete=models.CASCADE)
    month = models.CharField(max_length=30,default=0)
    date_range = models.CharField(max_length=50, default=0)
    year = models.CharField(max_length=4,default=0)
    pay_cycle = models.IntegerField(default=0)
    rate = models.DecimalField(default=0, decimal_places=2, max_digits=100)
    earnings_allowance = models.DecimalField(default=0, decimal_places=2, max_digits=100)
    deductions_tax = models.DecimalField(default=0, decimal_places=2, max_digits=100)
    deductions_health = models.DecimalField(default=0, decimal_places=2,max_digits=100)
    total_deductions = models.DecimalField(default=0, decimal_places=2, max_digits=100)
    pag_ibig = models.DecimalField(default=0, decimal_places=2,max_digits=100)
    sss = models.DecimalField(default=0, decimal_places=2,max_digits=100)
    overtime = models.DecimalField(default=0, decimal_places=2,max_digits=100)
    total_earnings = models.DecimalField(default=0, decimal_places=2,max_digits=100)
    total_pay = models.DecimalField(default=0, decimal_places=2,max_digits=100)
    
    def getIDNumber(self):
        return self.id_number
    
    def getMonth(self):
        return self.month

    def getDate_range(self):
        month_number = list(calendar.month_name).index(self.month.capitalize())
        last_day = calendar.monthrange(int(self.year), month_number)[1]
        
        if self.pay_cycle == 1: 
            self.date_range = "1-15" 
        elif self.pay_cycle == 2: 
            self.date_range = f"16-{last_day}"

        return self.date_range
    
    def getYear(self):
        return self.year
    
    def getPay_cycle(self):
        return self.pay_cycle
    
    def getRate(self):
        self.rate = self.id_number.rate
        return self.rate
    
    def getCycleRate(self):
        return self.rate*0.5
    
    def getEarnings_allowance(self):
        self.earnings_allowance = self.id_number.allowance
        self.earnings_allowance = round(self.earnings_allowance,2)
        return self.earnings_allowance
    
    def getOvertime(self):
        self.overtime = self.id_number.overtime_pay 
        self.overtime = round(self.overtime,2)
        # print(f"getOvertime: {self.overtime}")
        return self.overtime
    
    def getDeductions_tax(self): 
        if self.pay_cycle == 1:
            self.deductions_tax = ((self.rate / 2) + self.id_number.allowance + self.id_number.overtime_pay - self.getPag_ibig()) * 0.2
        elif self.pay_cycle == 2:
            self.deductions_tax = ((self.rate / 2) + self.id_number.allowance + self.id_number.overtime_pay - self.getDeductions_health() - self.getSSS()) * 0.2
        self.deductions_tax=round(self.deductions_tax,2)
        if self.deductions_tax < 0:
            self.deductions_tax = 0

        return self.deductions_tax
    
    def getDeductions_health(self):
        if self.pay_cycle == 2: 
            self.deductions_health = self.rate * 0.04
        else: 
            self.deductions_health = 0
        self.deductions_health = round(self.deductions_health,2)
        return self.deductions_health


    def getTotalDeductions(self):
        if self.pay_cycle == 1:
            self.total_deductions = float(self.deductions_tax) + float(self.pag_ibig) 
        elif self.pay_cycle == 2:
            self.total_deductions = float(self.deductions_tax) + float(self.getDeductions_health()) + float(self.sss)
        self.total_deductions=round(self.total_deductions,2)

        return self.total_deductions

    def getPag_ibig(self):
        if self.pay_cycle == 1: 
            self.pag_ibig = 100
        else: 
            self.pag_ibig = 0
        return self.pag_ibig
        
    def getSSS(self):
        if self.pay_cycle == 2:
            self.sss = self.rate * 0.045
        else:
            self.sss = 0 
        self.sss = round(self.sss,2)
        return self.sss
        
    def getGrossPay(self):
        self.total_earnings = float(self.rate) + float(self.earnings_allowance) + float(self.getOvertime())
        return self.total_earnings
    
    def getTotal_pay(self):
        if self.pay_cycle == 1: 
            self.total_pay = ((self.rate / 2) + self.getEarnings_allowance() + self.getOvertime() - self.getPag_ibig()) - self.getDeductions_tax()
        elif self.pay_cycle == 2: 
            self.total_pay = ((self.rate / 2) + self.getEarnings_allowance() + self.getOvertime() - self.getDeductions_health() - self.getSSS()) - self.getDeductions_tax()
        self.total_pay = round(self.total_pay,2)
        # print(f"Total_pay: {self.getOvertime()}")
        # print(f"Total_pay: {self.total_pay}")
        if self.total_pay < 0:
            self.total_pay = 0
        return self.total_pay
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.getDate_range()
        self.getRate()
        self.getCycleRate()
        self.getEarnings_allowance()
        self.getDeductions_tax()
        self.getDeductions_health
        self.getPag_ibig()
        self.getSSS()
        self.id_number.getOvertimePay()
        self.getOvertime()
        self.getTotal_pay()
        self.getGrossPay()
        self.getTotalDeductions()

        return 
    
    def __str__(self):
        return f"pk: {self.pk}, Employee ID Number: {self.id_number.id_number}, Period: {self.month} {self.date_range}, {self.year}, Cycle: {self.pay_cycle}, Total Pay: {self.total_pay}"