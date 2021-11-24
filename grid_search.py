import random
import re
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.metrics import roc_auc_score, precision_recall_curve, roc_curve, average_precision_score
from sklearn.model_selection import KFold
from lightgbm import LGBMClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import gc
train_data = pd.read_csv('raw_data/train_public.csv')
submit_example = pd.read_csv('raw_data/submit_example.csv')
test_public = pd.read_csv('raw_data/test_public.csv')
train_inte = pd.read_csv('raw_data/train_internet.csv')
from sklearn.model_selection import GridSearchCV
def workYearDIc(x):
    if str(x) == 'nan':
        return -1
    x = x.replace('< 1', '0')
    return int(re.search('(\d+)', x).group())


def findDig(val):
    fd = re.search('(\d+-)', val)
    if fd is None:
        return '1-' + val
    return val + '-01'

random.seed(44444444)
def clear_early_return(temp):
    #k=temp.loc[:,['early_return', 'early_return_amount', 'early_return_amount_3mon']]
    for index in range(len(temp)):
        if temp.early_return[index] == 0 and temp.early_return_amount[index] > 0:
            temp.early_return[index] = random.randint(1,3)
        if temp.early_return[index] == 0 and temp.early_return_amount_3mon[index] > 0:
            temp.early_return[index] = random.randint(1,3)
def clean_test(tmp):
    for index in range(len(tmp)):
        if tmp.early_return[index] != 0 and tmp.early_return_amount[index] == 0:
            tmp.early_return_amount[index]=random.uniform(1000,tmp.total_loan[index])

clear_early_return(train_data)
clear_early_return(test_public)
clear_early_return(train_inte)
clean_test(test_public)

class_dict = {
    'A': 1,
    'B': 2,
    'C': 3,
    'D': 4,
    'E': 5,
    'F': 6,
    'G': 7,
}
timeMax = pd.to_datetime('1-Dec-21')
train_data['work_year'] = train_data['work_year'].map(workYearDIc)
test_public['work_year'] = test_public['work_year'].map(workYearDIc)
train_data['class'] = train_data['class'].map(class_dict)
test_public['class'] = test_public['class'].map(class_dict)
# # f=['f0','f1','f3','f4','f2']
# # train_data[f].fillna(0)
# # train_inte[f].fillna(0)
# # test_public[f].fillna(0)
# train_data["pub_dero_bankrup"] = train_data["pub_dero_bankrup"].fillna(train_data["pub_dero_bankrup"].median())
train_data['pro']=train_data['interest']*train_data['year_of_loan']
test_public['pro']=test_public['interest']*test_public['year_of_loan']
train_inte['pro']=train_inte['interest']*train_inte['year_of_loan']
train_data['loan_year']=train_data['total_loan']/train_data['year_of_loan']
test_public['loan_year']=test_public['total_loan']/test_public['year_of_loan']
train_inte['loan_year']=train_inte['total_loan']/train_inte['year_of_loan']
train_data['early_ratio']=train_data['early_return_amount']/train_data['total_loan']
test_public['early_ratio']=test_public['early_return_amount']/test_public['total_loan']
train_inte['early_ratio']=train_inte['early_return_amount']/train_inte['total_loan']
train_data['early_times_ratio']=train_data['early_return']/train_data['year_of_loan']
test_public['early_times_ratio']=test_public['early_return']/test_public['year_of_loan']
train_inte['early_times_ratio']=train_inte['early_return']/train_inte['year_of_loan']
train_data['recircle_ratio']=train_data['recircle_b']/train_data['total_loan']
test_public['recircle_ratio']=test_public['recircle_b']/test_public['total_loan']
train_inte['recircle_ratio']=train_inte['recircle_b']/train_inte['total_loan']
train_data['recircle_amt']=train_data['recircle_u']*train_data['total_loan']
test_public['recircle_amt']=test_public['recircle_u']*test_public['total_loan']
train_inte['recircle_amt']=train_inte['recircle_u']*train_inte['total_loan']
train_data['earlies_credit_mon'] = pd.to_datetime(train_data['earlies_credit_mon'].map(findDig))
test_public['earlies_credit_mon'] = pd.to_datetime(test_public['earlies_credit_mon'].map(findDig))
train_data.loc[train_data['earlies_credit_mon'] > timeMax, 'earlies_credit_mon'] = train_data.loc[train_data['earlies_credit_mon'] > timeMax, 'earlies_credit_mon'] + pd.offsets.DateOffset(years=-100)
test_public.loc[test_public['earlies_credit_mon'] > timeMax, 'earlies_credit_mon'] = test_public.loc[test_public['earlies_credit_mon'] > timeMax, 'earlies_credit_mon'] + pd.offsets.DateOffset(years=-100)
train_data['issue_date'] = pd.to_datetime(train_data['issue_date'])
test_public['issue_date'] = pd.to_datetime(test_public['issue_date'])

# Internet数据处理
train_inte['work_year'] = train_inte['work_year'].map(workYearDIc)
train_inte['class'] = train_inte['class'].map(class_dict)
train_inte['earlies_credit_mon'] = pd.to_datetime(train_inte['earlies_credit_mon'])
train_inte['issue_date'] = pd.to_datetime(train_inte['issue_date'])

train_data['issue_date_month'] = train_data['issue_date'].dt.month
test_public['issue_date_month'] = test_public['issue_date'].dt.month
train_data['issue_date_dayofweek'] = train_data['issue_date'].dt.dayofweek
test_public['issue_date_dayofweek'] = test_public['issue_date'].dt.dayofweek

train_data['earliesCreditMon'] = train_data['earlies_credit_mon'].dt.month
test_public['earliesCreditMon'] = test_public['earlies_credit_mon'].dt.month
train_data['earliesCreditYear'] = train_data['earlies_credit_mon'].dt.year
test_public['earliesCreditYear'] = test_public['earlies_credit_mon'].dt.year

###internet数据

train_inte['issue_date_month'] = train_inte['issue_date'].dt.month
train_inte['issue_date_dayofweek'] = train_inte['issue_date'].dt.dayofweek
train_inte['earliesCreditMon'] = train_inte['earlies_credit_mon'].dt.month
train_inte['earliesCreditYear'] = train_inte['earlies_credit_mon'].dt.year

cat_cols = ['employer_type', 'industry']

from sklearn.preprocessing import LabelEncoder

for col in cat_cols:
    lbl = LabelEncoder().fit(train_data[col])
    train_data[col] = lbl.transform(train_data[col])
    test_public[col] = lbl.transform(test_public[col])

    # Internet处理
    train_inte[col] = lbl.transform(train_inte[col])

# 'f1','policy_code','app_type' 这三个去掉是881
# ,'f1','policy_code','app_type'
col_to_drop = ['issue_date', 'earlies_credit_mon','policy_code']
train_data = train_data.drop(col_to_drop, axis=1)
test_public = test_public.drop(col_to_drop, axis=1)

##internet处理
train_inte = train_inte.drop(col_to_drop, axis=1)
# 暂时不变
# train_inte = train_inte.rename(columns={'is_default':'isDefault'})
# data = pd.concat( [train_data,test_public] )
tr_cols = set(train_data.columns)
same_col = list(tr_cols.intersection(set(train_inte.columns)))
train_inteSame = train_inte[same_col].copy()

Inte_add_cos = list(tr_cols.difference(set(same_col)))
for col in Inte_add_cos:
    train_inteSame[col] = np.nan

# 81后加
for col in cat_cols:
    dum = pd.get_dummies(data[col], prefix='OneHot_'+col +'_')
    data = pd.concat([data, dum], axis=1)
#     del data[col]
    del dum
f=['f0','f1','f3','f4','f2']
im=KNNImputer(n_neighbors=5)
train_data=im.fit_transform(train_data)


# y=train_data['isDefault']
#
# X_train1 = train_data.drop(['isDefault','loan_id','user_id'], axis = 1, inplace = False)
# param_grid = [
#     {'learning_rate': [0.01, 0.008,0.006], ' reg_alpha': [0.1,0.3,0.5],'reg_lambda':[0.1,0.3,0.5],
#      'num_thread':[10,30,50],'n_estimators':[4000,6000],'subsample':[0.45,0.55,0.65]}
# ]
#
# forest_reg = LGBMClassifier()
# grid_search = GridSearchCV(forest_reg, param_grid, cv=5,
#                            scoring='neg_mean_squared_error')
#
# grid_search.fit(train_data, y)
# print(grid_search.best_estimator_)