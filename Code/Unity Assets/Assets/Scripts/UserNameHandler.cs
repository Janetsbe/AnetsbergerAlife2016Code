using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class UserNameHandler : MonoBehaviour {

    public Vector3 initialPosition;
    public string userName;
    int time;
    public int duration;
    public Transform parentCommandLabel;


	// Use this for initialization
	void Start () {
        transform.SetParent(parentCommandLabel);
        transform.position = initialPosition;
        gameObject.GetComponent<Text>().text = userName;
        gameObject.name = userName + " popup";
        time = 0;

        duration = (int)(duration * Time.timeScale);
    
	
	}
	
	// Update is called once per frame
	void Update () {
	
	}

    void IncrementCountText() {
        int count = int.Parse(parentCommandLabel.Find("count").GetComponent<Text>().text);
        count += 1;
        float barLength = CalculateBarLength(count);
        parentCommandLabel.Find("count").GetComponent<Text>().text = count.ToString();
        parentCommandLabel.Find("bar").GetComponent<RectTransform>().sizeDelta = new Vector2(barLength, 30);
    }

    float CalculateBarLength(int count) {
        float length = 15f + Mathf.Atan(count / 100f) * (-70f + duration);
        return length;
    }

    void FixedUpdate() {
        time += 1;
        if(time >= duration) {
            EndPopup();
        }
        transform.localPosition -= new Vector3(1.6f/Time.timeScale, 0f, 0f);
        float scale = -Mathf.Atan(((float)time - duration) / 25) / (Mathf.PI / 2);
        //print(scale);
        transform.localScale = scale * Vector3.one;

        float rgb = (float)time / duration;
        gameObject.GetComponent<Text>().color = new Color(rgb, rgb, rgb);

    }

    void EndPopup() {
        IncrementCountText();
        Destroy(gameObject);
    }

    void OnTriggerEnter2D(Collider2D col) {
        if (col.gameObject.name.Equals("bar")) {
            EndPopup();
        }
    }

}
