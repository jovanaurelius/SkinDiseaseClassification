import numpy as np 
import cv2 
import os
import re
import pandas as pd 
import seaborn as sns
from skimage import color
from skimage import io
from matplotlib import pyplot as plt
import matplotlib.image as mpimg    
from skimage.feature import greycomatrix, greycoprops   
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from sklearn import svm, datasets
from sklearn.svm import SVC  
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import GridSearchCV

# -------------------- Utility function ------------------------
def normalize_label(str_):
    str_ = str_.replace(" ", "")
    str_ = str_.translate(str_.maketrans("","", "()"))
    str_ = str_.split("_")
    return ''.join(str_[:2])

def normalize_desc(folder, sub_folder):
    text = folder + " - " + sub_folder 
    text = re.sub(r'\d+', '', text)
    text = text.replace(".", "")
    text = text.strip()
    return text

def print_progress(val, val_len, folder, sub_folder, filename, bar_size=10):
    progr = "#"*round((val)*bar_size/val_len) + " "*round((val_len - (val))*bar_size/val_len)
    if val == 0:
        print("", end = "\n")
    else:
        print("[%s] folder : %s/%s/ ----> file : %s" % (progr, folder, sub_folder, filename), end="\r")
        

#Load Dataset and store in array
 
dataset_dir = "/content/drive/" #Input file directory of new dataset to test

imgs_input = [] #to store images data
labels = [] #to store images labels
descs = []
for folder in os.listdir(dataset_dir):
    for sub_folder in os.listdir(os.path.join(dataset_dir, folder)):
        sub_folder_files = os.listdir(os.path.join(dataset_dir, folder, sub_folder))
        len_sub_folder = len(sub_folder_files) - 1
        for i, filename in enumerate(sub_folder_files):
            img = cv2.imread(os.path.join(dataset_dir, folder, sub_folder, filename))
            
            resize = cv2.resize(img, (300,300)) #Resize the image to 300x300

            imgs_input.append(resize)
            labels.append(sub_folder) #Append labels may vary based on where the folder shows the label for each data
            descs.append(normalize_desc(folder, sub_folder))
            
            print_progress(i, len_sub_folder, folder, sub_folder, filename)

label2 = labels      
#images data were stored in array imgs_input    

#Loop to identify area of skin disease for each images
for i in range(len(imgs_input)):
  original_image = imgs_input[i]
  img=cv2.cvtColor(original_image,cv2.COLOR_BGR2RGB)
  vectorized = img.reshape((-1,3))
  vectorized = np.float32(vectorized)
  criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.01)
  k = 3 #3 clusters used
  _, labels, (centers) = cv2.kmeans(vectorized, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
  # convert back to 8 bit values
  centers = np.uint8(centers)

  # flatten the labels array
  labels = labels.flatten()

  img_new = np.copy(img)
  img_new = img_new.reshape((-1, 3))
  List = labels.tolist() #convert labels array to list
  clusterss = most_frequent(List)
  img_new[labels == clusterss] = [0, 0, 0] #remove largest cluster from each images to identify affected area
  img_new = img_new.reshape(img.shape)
  img_new = img_new.reshape(img.shape)

  imgs_input[i] = img_new

#Loop to convert each data to grayscale image
for i in range(len(imgs_input)):
  img = imgs_input[i]
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  imgs_input[i] = gray

# ----------------- calculate greycomatrix() & greycoprops() for angle 0, 45, 90, 135 ----------------------------------
def calc_glcm_all_agls(img, label, props, dists=[5], agls=[0, np.pi/4, np.pi/2, 3*np.pi/4], lvl=256, sym=True, norm=True):
    
    glcm = greycomatrix(img, 
                        distances=dists, 
                        angles=agls, 
                        levels=lvl,
                        symmetric=sym, 
                        normed=norm)
    feature = []
    glcm_props = [propery for name in props for propery in greycoprops(glcm, name)[0]]
    for item in glcm_props:
            feature.append(item)
    feature.append(label) 
    
    return feature


# ----------------- call calc_glcm_all_agls() for all properties ----------------------------------
properties = ['dissimilarity', 'correlation', 'homogeneity', 'contrast', 'ASM', 'energy']

glcm_all_agls = []
for img, label in zip(imgs_input, label2): 
    glcm_all_agls.append(
            calc_glcm_all_agls(img, 
                                label, 
                                props=properties)
                            )
 
columns = []
angles = ['0', '45', '90','135']
for name in properties :
    for ang in angles:
        columns.append(name + "_" + ang)
        
columns.append("label")

# Create the pandas DataFrame for GLCM features data
glcm_df_new = pd.DataFrame(glcm_all_agls, 
                      columns = columns)

glcm_df_new.head(7)
glcm_df_new['label'].value_counts()

glcm_df_new['label'].replace({"pigmented benign keratosis": 0, "melanoma": 1, "squamous cell carcinoma" : 2}, inplace=True)
print(glcm_df_new)

#Normalize the feature data
glcm_df_new[["dissimilarity_0", "dissimilarity_45", "dissimilarity_90", "dissimilarity_135", "correlation_0", "correlation_45", "correlation_90", "correlation_135", "homogeneity_0", "homogeneity_45", "homogeneity_90", "homogeneity_135", "contrast_0", "contrast_45", "contrast_90", "contrast_135", "ASM_0", "ASM_45", "ASM_90", "ASM_135", "energy_0", "energy_45", "energy_90", "energy_135"]] = min_max_scaler.fit_transform(glcm_df_new[["dissimilarity_0", "dissimilarity_45", "dissimilarity_90", "dissimilarity_135", "correlation_0", "correlation_45", "correlation_90", "correlation_135", "homogeneity_0", "homogeneity_45", "homogeneity_90", "homogeneity_135", "contrast_0", "contrast_45", "contrast_90", "contrast_135", "ASM_0", "ASM_45", "ASM_90", "ASM_135", "energy_0", "energy_45", "energy_90", "energy_135"]])

#Select x and y
X1 = glcm_df_new[['dissimilarity_0', 'dissimilarity_45','dissimilarity_90','dissimilarity_135','correlation_0','correlation_45','correlation_90','correlation_135','homogeneity_0', 'homogeneity_45','homogeneity_90','homogeneity_135','contrast_0','contrast_45','contrast_90','contrast_135','ASM_0','ASM_45','ASM_90','ASM_135','energy_0','energy_45','energy_90','energy_135']].values
y = glcm_df_new['label']

#Classify using best model obtained before
rbf_pred = rbf.predict(X1)
accuracy_rbf = rbf.score(X1, y)
print("Accuracy Radial Basis Kernel:", accuracy_rbf)
print(classification_report(y, rbf_pred))

#Print confusion matrix
cm = confusion_matrix(y, rbf_pred)

plt.figure (figsize=(10,7))
sn.heatmap(cm, annot=True)
plt.xlabel('Predicted')
plt.ylabel('Truth')