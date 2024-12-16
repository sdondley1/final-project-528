import os
import glob
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import seaborn as sns
import matplotlib.pyplot as plt
import joblib



# PROJ FOLDER - CHANGE THIS TO UR FOLDER
project_folder = r"/Users/sean/umass/cs528/final_project_new/data"

dataframes = []
labels = []

for label_folder in os.listdir(project_folder):
    label_path = os.path.join(project_folder, label_folder)
    
    if os.path.isdir(label_path):
        for partner_folder in os.listdir(label_path):
            partner_path = os.path.join(label_path, partner_folder)
            
            if os.path.isdir(partner_path): 
                for csv_file in glob.glob(os.path.join(partner_path, "*.csv")):
                    df = pd.read_csv(csv_file).to_numpy() 
                    
                    dataframes.append(df)
                    labels.append(label_folder)

high_len = max(len(arr) for arr in dataframes)
data_combined = np.array([np.pad(arr, ((0, high_len - len(arr)), (0, 0)), mode='constant') for arr in dataframes])

all_data_df_combined = pd.DataFrame(data_combined.reshape(len(data_combined), -1))

labels_series_combined = pd.Series(labels)

x_train, x_test, y_train, y_test = train_test_split(
    all_data_df_combined, labels_series_combined, stratify=labels_series_combined, test_size=0.3, random_state=9
)

model = SVC(kernel='rbf')
model.fit(x_train, y_train)
y_pred = model.predict(x_test)


accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy}")
print("Classification Report:")
print(classification_report(y_test, y_pred))

conf_matrix = confusion_matrix(y_test, y_pred)
sns.heatmap(conf_matrix, annot=True, cmap="Blues", fmt='d', xticklabels=model.classes_, yticklabels=model.classes_)

plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

joblib.dump(model, "drone_svm_model.pkl")
#loaded_model = joblib.load("drone_svm_model.pkl")
