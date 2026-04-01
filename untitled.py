print("hello world")

name = "Rajesh Hamal"
print(name)
print(20+40)
username = "ram123"
password = "password@123"
user_input = input("enter your username:")
user_password = input("enter your password:")
if user_input == username and user_password == password:
    print("welcome to the dashboard")
    new_age = input("enter your age:")

    if int(new_age) <= 17:
     print("you are not eligibe for the trail")
    else:
     print("pay fee and give trail")

else:
 print("Sorry worng username and password")
for i in range(10):
    for j in range(5):
        print(i,"*",j,"=",i*j)

        fav_fruits= ['mango', 'banana', 'watermelon']
        for i in fav_fruits:
            print(i)  
