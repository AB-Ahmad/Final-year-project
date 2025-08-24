import React, { useState, useEffect } from "react";
import { View, Text, FlatList, StyleSheet, TouchableOpacity, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system";
import * as Sharing from "expo-sharing";
import { Swipeable } from "react-native-gesture-handler";

export default function ResultsScreen() {
  const [results, setResults] = useState([]);

  useEffect(() => {
    const loadResults = async () => {
      try {
        const stored = await AsyncStorage.getItem("gradedResults");
        setResults(stored ? JSON.parse(stored) : []);
      } catch (error) {
        console.error("Error loading results:", error);
      }
    };
    loadResults();
  }, []);

  // 🔹 Convert results to CSV
  const exportToCSV = async () => {
    if (results.length === 0) {
      Alert.alert("No Results", "There are no graded results to export.");
      return;
    }

    let csv = "RegNumber,Course,Score,Total,Timestamp\n";
    results.forEach(r => {
      csv += `${r.reg_number},${r.courseCode},${r.score},${r.total},${r.timestamp}\n`;
    });

    try {
      const fileUri = FileSystem.documentDirectory + "graded_results.csv";
      await FileSystem.writeAsStringAsync(fileUri, csv, { encoding: FileSystem.EncodingType.UTF8 });

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri);
      } else {
        Alert.alert("Exported", `CSV saved at ${fileUri}`);
      }
    } catch (error) {
      console.error("CSV export error:", error);
      Alert.alert("Error", "Failed to export CSV file.");
    }
  };

  // 🔹 Delete a single result
  const deleteResult = async (index) => {
    try {
      const updated = [...results];
      updated.splice(index, 1);
      setResults(updated);
      await AsyncStorage.setItem("gradedResults", JSON.stringify(updated));
    } catch (error) {
      console.error("Error deleting result:", error);
      Alert.alert("Error", "Failed to delete result.");
    }
  };

  // 🔹 Clear all results
  const clearResults = async () => {
    Alert.alert(
      "Confirm",
      "Are you sure you want to delete all results?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete All",
          style: "destructive",
          onPress: async () => {
            try {
              await AsyncStorage.removeItem("gradedResults");
              setResults([]);
              Alert.alert("Success", "All results have been cleared.");
            } catch (error) {
              console.error("Error clearing results:", error);
              Alert.alert("Error", "Failed to clear results.");
            }
          },
        },
      ]
    );
  };

  // 🔹 Right action for swipe-to-delete
  const renderRightActions = (index) => (
    <TouchableOpacity
      style={styles.deleteButton}
      onPress={() => deleteResult(index)}
    >
      <Text style={styles.deleteText}>🗑️ Delete</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>📊 Grading Results</Text>

      <FlatList
        data={results}
        keyExtractor={(item, index) => index.toString()}
        renderItem={({ item, index }) => (
          <Swipeable renderRightActions={() => renderRightActions(index)}>
            <View style={styles.card}>
              <Text style={styles.course}>{item.courseCode}</Text>
              <Text>Reg: {item.reg_number}</Text>
              <Text>Score: {item.score}/{item.total}</Text>
              <Text style={styles.timestamp}>{item.timestamp}</Text>
            </View>
          </Swipeable>
        )}
      />

      {/* 🔹 Export Button */}
      <TouchableOpacity style={styles.exportButton} onPress={exportToCSV}>
        <Text style={styles.exportButtonText}>📤 Export to CSV</Text>
      </TouchableOpacity>

      {/* 🔹 Clear Results Button */}
      <TouchableOpacity style={styles.clearButton} onPress={clearResults}>
        <Text style={styles.clearButtonText}>🗑️ Clear All Results</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "white" },
  title: { fontSize: 22, fontWeight: "bold", marginBottom: 20 },
  card: {
    backgroundColor: "#f3f4f6",
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  course: { fontSize: 18, fontWeight: "bold" },
  timestamp: { fontSize: 12, color: "#666", marginTop: 5 },
  exportButton: {
    backgroundColor: "#3b82f6",
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 20,
  },
  exportButtonText: { color: "white", fontWeight: "bold", fontSize: 16 },
  clearButton: {
    backgroundColor: "#ef4444", // red
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 10,
  },
  clearButtonText: { color: "white", fontWeight: "bold", fontSize: 16 },
  deleteButton: {
    backgroundColor: "#ef4444",
    justifyContent: "center",
    alignItems: "flex-end",
    paddingHorizontal: 20,
    marginBottom: 10,
    borderRadius: 10,
  },
  deleteText: { color: "white", fontWeight: "bold" },
});
