using UnityEngine;
using System.Collections;

public class SensorHandler : MonoBehaviour {

    public int value;
    public int parentIndex;

	// Use this for initialization
	void Start () {
        value = 0;
	}
	
	// Update is called once per frame
	void Update () {
        	
	}

    void OnCollisionEnter(Collision col) {
        if(col.gameObject.name.Equals("floor")) {
            value = 1;
        }
    }
    void OnCollisionExit(Collision col) {
        if(col.gameObject.name.Equals("floor")) {
            value = 0;
        }
    }
}
