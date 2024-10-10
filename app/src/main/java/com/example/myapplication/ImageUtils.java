package com.example.myapplication;

import android.graphics.Bitmap;
import android.graphics.Color;
import android.util.Log;

public class ImageUtils {
    public static String calculatepHash(Bitmap image) {
        // 1. 将图像缩小到8x8
        Bitmap resizedImage = Bitmap.createScaledBitmap(image, 8, 8, false);

        // 2. 转换为灰度图像
        Bitmap grayImage = toGrayscale(resizedImage);

        // 3. 计算DCT
        int[] dctCoefficients = dct(grayImage);

        // 4. 计算平均值
        int average = calculateAverage(dctCoefficients);

        // 5. 生成哈希值
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 8 * 8; i++) {
            int pixel = dctCoefficients[i];
            sb.append((pixel > average) ? "1" : "0");
        }

        return sb.toString();
    }

    private static Bitmap toGrayscale(Bitmap image) {
        int width = image.getWidth();
        int height = image.getHeight();
        int[] pixels = new int[width * height];
        image.getPixels(pixels, 0, width, 0, 0, width, height);

        for (int i = 0; i < pixels.length; i++) {
            int gray = (int) (Color.red(pixels[i]) * 0.3 + Color.green(pixels[i]) * 0.59 + Color.blue(pixels[i]) * 0.11);
            pixels[i] = gray | (gray << 8) | (gray << 16) | 0xFF000000;
        }

        Bitmap grayscaleBitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        grayscaleBitmap.setPixels(pixels, 0, width, 0, 0, width, height);
        return grayscaleBitmap;
    }

    private static int[] dct(Bitmap image) {
        int width = image.getWidth();
        int height = image.getHeight();
        int[] pixels = new int[width * height];
        image.getPixels(pixels, 0, width, 0, 0, width, height);

        int[] dct = new int[width * height];
        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                double sum = 0.0;
                for (int i = 0; i < width; i++) {
                    for (int j = 0; j < height; j++) {
                        double cosx = (x == 0) ? 1.0 / Math.sqrt(width) : Math.cos((2 * i + 1) * x * Math.PI / (2 * width));
                        double cosy = (y == 0) ? 1.0 / Math.sqrt(height) : Math.cos((2 * j + 1) * y * Math.PI / (2 * height));
                        sum += pixels[i * height + j] * cosx * cosy;
                    }
                }
                dct[x * height + y] = (int) sum;
            }
        }
        return dct;
    }

    private static int calculateAverage(int[] dctCoefficients) {
        int sum = 0;
        for (int coeff : dctCoefficients) {
            sum += coeff;
        }
        return sum / (8 * 8);
    }

    public static int hammingDistance(String s1, String s2) {
        int distance = 0;
        for (int i = 0; i < s1.length(); i++) {
            if (s1.charAt(i) != s2.charAt(i)) {
                distance++;
            }
        }
        return distance;
    }
}