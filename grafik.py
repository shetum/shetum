import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

data = np.random.normal(size=100_000, scale = 1.5)
df = pd.DataFrame(data)

sns.ecdfplot(data)

# plt.hist(df[0], bins=500, density=True)
# plt.xlabel('Value')
# plt.ylabel('Frequency')
# plt.title('Normal Distribution')
plt.show()
