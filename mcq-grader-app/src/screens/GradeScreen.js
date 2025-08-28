// GradeScreen.js
import React, { useState } from "react";
import {
  View,
  Text,
  Image,
  ActivityIndicator,
  Alert,
  StyleSheet,
  TouchableOpacity,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";
import { BASE_URL } from "../../config";
import * as FileSystem from 'expo-file-system';

export default function GradeScreen({ route, navigation }) {
  const { template, courseCode } = route.params; // ✅ passed from TemplatesScreen
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  // Pick image from gallery
  const pickImage = async () => {
    let permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert(
        "Permission Required",
        "Please allow access to your photo library."
      );
      return;
    }

    let result = await ImagePicker.launchImageLibraryAsync({
      allowsEditing: false,
      quality: 1,
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
    });

    if (!result.canceled) {
      setImage(result.assets[0].uri);
    }
  };

  // Upload & Grade Image
  const gradeImage = async () => {
    if (!image) {
      Alert.alert("No Image Selected", "Please select an image first.");
      return;
    }

    setLoading(true);
    try {
      // Read image as base64
      const filename = image.split('/').pop();
      const base64 = await FileSystem.readAsStringAsync(image, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Send base64 to backend
      const response = await fetch(`${BASE_URL}/grade_base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          filename: filename,
          content: base64,
        }),
      });

      const data = await response.json();
      if (!data || !data.answers) {
        throw new Error("Invalid grading response");
      }

      // 🔹 Compare answers against template
      const details = [];
      let score = 0;
      template.forEach((correct, idx) => {
        const marked = data.answers[idx] || "";
        let status = "Blank";
        if (marked) {
          if (marked === correct) {
            status = "Correct ✅";
            score++;
          } else {
            status = `Wrong ❌ (marked ${marked})`;
          }
        }
        details.push({ question: idx + 1, marked, correct, status });
      });

      const result = {
        reg_number: data.reg_number || "UNKNOWN",
        score,
        total: template.length,
        courseCode,
        timestamp: new Date().toLocaleString(),
        details,
        debug_image: data.debug_image || null,
      };

      // Save result locally
      const existing = await AsyncStorage.getItem("gradedResults");
      const results = existing ? JSON.parse(existing) : [];
      results.push(result);
      await AsyncStorage.setItem("gradedResults", JSON.stringify(results));

      // Navigate to results screen
      navigation.navigate("GradingResult", { result });
    } catch (error) {
      console.error("Upload failed:", error);
      Alert.alert("Upload failed", error.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.courseCode}>Course: {courseCode}</Text>

      <TouchableOpacity
        style={[styles.button, { backgroundColor: "#3b82f6" }]}
        onPress={pickImage}
      >
        <Text style={styles.buttonText}>📷 Pick an Image</Text>
      </TouchableOpacity>

      {image && (
        <>
          <Image source={{ uri: image }} style={styles.imagePreview} />
          <TouchableOpacity
            style={[styles.button, { backgroundColor: "#10b981" }]}
            onPress={gradeImage}
          >
            <Text style={styles.buttonText}>✅ Upload & Grade</Text>
          </TouchableOpacity>
        </>
      )}

      {loading && (
        <ActivityIndicator
          size="large"
          color="#3b82f6"
          style={{ marginTop: 20 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "white" },
  courseCode: { fontSize: 20, fontWeight: "bold", marginBottom: 20 },
  button: {
    padding: 15,
    borderRadius: 10,
    marginVertical: 10,
    alignItems: "center",
  },
  buttonText: { color: "white", fontWeight: "bold", fontSize: 16 },
  imagePreview: {
    width: "100%",
    height: 450, // ✅ full height preview
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#ccc",
    marginVertical: 15,
    resizeMode: "contain", // ✅ prevents cropping
  },
});
