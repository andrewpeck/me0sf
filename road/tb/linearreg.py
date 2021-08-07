#Two samples of the linear regression software
import matplotlib.pyplot as plt
import random

#standard excel-esque style; uses linear least squares method and lists of data values
def best_fit(x_data,y_data):
    sum_x=sum(x_data)
    sum_y=sum(y_data)
    n=len(x_data)
    xy_list=[]
    x_sq_list=[]
    for i in range(len(x_data)):
        xy_list.append(x_data[i]*y_data[i])
        x_sq_list.append(x_data[i]**2)
    sum_xy=sum(xy_list)
    sum_x_sq=sum(x_sq_list)
    slope=(n*sum_xy-(sum_x*sum_y))/(n*sum_x_sq-sum_x**2)
    b=(sum_y-slope*sum_x)/n
    y_fit=[]
    for j in range(len(y_data)):
        y_fit.append(slope*x_data[j]+b)
    slope=round(slope,4)
    b=round(b,4)
    return slope, b, y_fit

def print_my_best_fit(slope,b,x_data,y_data,y_fit):
    string='y='+str(slope)+'+'+str(b)
    plt.plot(x_data,y_data,'o')
    plt.plot(x_data,y_fit,'k-',label=string)
    plt.title('Sample Data')
    plt.legend()
    plt.show()


