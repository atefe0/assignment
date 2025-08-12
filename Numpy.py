import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, ifft2, fftshift, ifftshift

N = 256
img = np.zeros((N,N), dtype=float)

yy, xx = np.ogrid[:N,:N]

circle = (xx-N//2)**2 + (yy-N//2)**2 <= (N//6)**2
img[circle] = 1.0

img[N//4:N//4+40, N//4:N//4+40] = 0.7

ring = ((xx-3*N//4)**2 + (yy-N//4)**2 <= (N//8)**2) & \
((xx-3*N//4)**2+(yy-N//4)**2>= (N//8-5)**2)
img[ring] = 0.9

support_mask = img > 0
fft_img = fftshift(fft2(img))
magnitude_full = np.abs(fft_img)

sampling_rate = 0.6
freq_mask = np.zeros_like(img, dtype=bool)
num_samples = int(sampling_rate*N*N)
idx = np.random.choice(N*N, num_samples, replace=False)
freq_mask.flat[idx] = True

M = np.zeros_like(img)
M[freq_mask] = magnitude_full[freq_mask]

noise_sigma = 0.02
M[freq_mask] += noise_sigma * np.max(magnitude_full) * np.random.randn(np.sum(freq_mask))

def gerchberg_saxton(M, freq_mask, support_mask, iterations=500):
    phase = np.exp(1j*2*np.pi*np.random.rand(*M.shape))
    G = np.zeros_like(M, dtype=complex)
    G[freq_mask] = M[freq_mask] * phase[freq_mask]

    img_est = np.real(ifft2(ifftshift(G)))
    errors = []
    for it in range(iterations):
        img_est[~support_mask] = 0
        img_est = np.clip(img_est, 0, None)
        F_est = fftshift(fft2(img_est))

        phase_est = np.exp(1j*np.angle(F_est))
        F_est[freq_mask] = M[freq_mask]* phase_est[freq_mask]

        img_est = np.real(ifft2(ifftshift(F_est)))

        diff = np.linalg.norm(np.abs(F_est[freq_mask])- M[freq_mask]) / np.linalg.norm(M[freq_mask])
        errors.append(diff)
        return img_est, errors
    
reconstructed, errors = gerchberg_saxton(M, freq_mask, support_mask, iterations=500)

fig, axs = plt.subplots(2,3,figsize=(12,8))
axs[0,0].imshow(img, cmap="gray")
axs[0,0].set_title("Ground Truth")
axs[0,0].axis("off")

axs[0,1].imshow(support_mask, cmap="gray")
axs[0,1].set_title("Support Mask")
axs[0,1].axis("off")

axs[0,2].imshow(freq_mask, cmap="gray")
axs[0,2].set_title("Frequency Mask")
axs[0,2].axis("off")

axs[1,0].imshow(np.log1p(magnitude_full), cmap="gray")
axs[1,0].set_title("Log Magnitude")
axs[1,0].axis("off")

axs[1,1].imshow(reconstructed, cmap="gray")
axs[1,1].set_title("Reconstructed Image")
axs[1,1].axis("off")

axs[1,2].plot(errors)
axs[1,2].set_title("Errors vs Iteration")
axs[1,2].set_xlabel("Iteration")
axs[1,2].set_ylabel("Relative Errors")

plt.tight_layout()
plt.show()
